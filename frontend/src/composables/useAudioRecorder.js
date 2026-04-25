import { ref, onUnmounted } from 'vue'

export function useAudioRecorder() {
  const isRecording = ref(false)
  const audioLevel = ref(0)
  const hasPermission = ref(false)
  const errorMessage = ref('')
  
  let mediaRecorder = null
  let audioContext = null
  let analyser = null
  let audioChunks = []
  let levelAnimationId = null

  const arrayBufferToBase64 = (buffer) => {
    let binary = ''
    const bytes = new Uint8Array(buffer)
    const len = bytes.byteLength
    for (let i = 0; i < len; i++) {
      binary += String.fromCharCode(bytes[i])
    }
    return btoa(binary)
  }

  const downsampleBuffer = (buffer, inputSampleRate, outputSampleRate) => {
    if (outputSampleRate >= inputSampleRate) {
      return buffer
    }

    const sampleRateRatio = inputSampleRate / outputSampleRate
    const newLength = Math.round(buffer.length / sampleRateRatio)
    const result = new Float32Array(newLength)
    let offsetResult = 0
    let offsetBuffer = 0

    while (offsetResult < result.length) {
      const nextOffsetBuffer = Math.round((offsetResult + 1) * sampleRateRatio)
      let accum = 0
      let count = 0

      for (let i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i += 1) {
        accum += buffer[i]
        count += 1
      }

      result[offsetResult] = count > 0 ? accum / count : 0
      offsetResult += 1
      offsetBuffer = nextOffsetBuffer
    }

    return result
  }

  const floatTo16BitPCM = (view, offset, input) => {
    for (let i = 0; i < input.length; i += 1, offset += 2) {
      const sample = Math.max(-1, Math.min(1, input[i]))
      view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true)
    }
  }

  const encodeWav = (samples, sampleRate) => {
    const buffer = new ArrayBuffer(44 + samples.length * 2)
    const view = new DataView(buffer)
    const writeString = (target, offset, value) => {
      for (let i = 0; i < value.length; i += 1) {
        target.setUint8(offset + i, value.charCodeAt(i))
      }
    }

    writeString(view, 0, 'RIFF')
    view.setUint32(4, 36 + samples.length * 2, true)
    writeString(view, 8, 'WAVE')
    writeString(view, 12, 'fmt ')
    view.setUint32(16, 16, true)
    view.setUint16(20, 1, true)
    view.setUint16(22, 1, true)
    view.setUint32(24, sampleRate, true)
    view.setUint32(28, sampleRate * 2, true)
    view.setUint16(32, 2, true)
    view.setUint16(34, 16, true)
    writeString(view, 36, 'data')
    view.setUint32(40, samples.length * 2, true)
    floatTo16BitPCM(view, 44, samples)

    return buffer
  }

  const convertBlobToWavBase64 = async (audioBlob) => {
    const blobArrayBuffer = await audioBlob.arrayBuffer()
    const decodeContext = new (window.AudioContext || window.webkitAudioContext)()

    try {
      const audioBuffer = await decodeContext.decodeAudioData(blobArrayBuffer.slice(0))
      const channelData = audioBuffer.numberOfChannels > 1
        ? audioBuffer.getChannelData(0)
        : audioBuffer.getChannelData(0)
      const downsampled = downsampleBuffer(channelData, audioBuffer.sampleRate, 16000)
      const wavBuffer = encodeWav(downsampled, 16000)
      return arrayBufferToBase64(wavBuffer)
    } finally {
      await decodeContext.close()
    }
  }

  const requestPermission = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 16000
        } 
      })
      hasPermission.value = true
      errorMessage.value = ''
      stream.getTracks().forEach(track => track.stop())
      return true
    } catch (error) {
      hasPermission.value = false
      errorMessage.value = error.message || '无法获取麦克风权限'
      console.error('Microphone permission error:', error)
      return false
    }
  }

  const startRecording = async () => {
    if (isRecording.value) return false
    
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 16000
        } 
      })
      
      hasPermission.value = true
      audioChunks = []
      
      audioContext = new (window.AudioContext || window.webkitAudioContext)()
      const source = audioContext.createMediaStreamSource(stream)
      analyser = audioContext.createAnalyser()
      analyser.fftSize = 256
      source.connect(analyser)
      
      mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      })
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.push(event.data)
        }
      }
      
      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach(track => track.stop())
        if (audioContext) {
          audioContext.close()
          audioContext = null
        }
        if (levelAnimationId) {
          cancelAnimationFrame(levelAnimationId)
          levelAnimationId = null
        }
      }
      
      mediaRecorder.start(100)
      isRecording.value = true
      errorMessage.value = ''
      
      const updateLevel = () => {
        if (analyser && isRecording.value) {
          const dataArray = new Uint8Array(analyser.frequencyBinCount)
          analyser.getByteFrequencyData(dataArray)
          const average = dataArray.reduce((a, b) => a + b, 0) / dataArray.length
          audioLevel.value = Math.min(100, (average / 128) * 100)
          levelAnimationId = requestAnimationFrame(updateLevel)
        }
      }
      updateLevel()
      
      return true
    } catch (error) {
      isRecording.value = false
      errorMessage.value = error.message || '启动录音失败'
      console.error('Recording error:', error)
      return false
    }
  }

  const stopRecording = async () => {
    return new Promise((resolve) => {
      if (!isRecording.value || !mediaRecorder) {
        console.error('No active recording or mediaRecorder not initialized')
        resolve(null)
        return
      }
      
      mediaRecorder.onstop = async () => {
        try {
          console.log('Recording stopped, processing audio...')
          console.log('Audio chunks length:', audioChunks.length)
          
          if (audioChunks.length === 0) {
            console.error('No audio chunks recorded')
            resolve(null)
            return
          }
          
          const audioBlob = new Blob(audioChunks, { type: 'audio/webm' })
          console.log('Audio blob size:', audioBlob.size)
          
          if (audioBlob.size === 0) {
            console.error('Audio blob is empty')
            resolve(null)
            return
          }
          
          const base64 = await convertBlobToWavBase64(audioBlob)
          console.log('Base64 length:', base64.length)
          
          if (!base64 || base64.length === 0) {
            console.error('Base64 conversion failed')
            resolve(null)
            return
          }
          
          resolve(base64)
        } catch (error) {
          console.error('Error processing audio:', error)
          resolve(null)
        } finally {
          // 清理资源
          try {
            if (mediaRecorder && mediaRecorder.stream) {
              mediaRecorder.stream.getTracks().forEach(track => track.stop())
            }
          } catch (e) {
            console.error('Error stopping tracks:', e)
          }
          
          try {
            if (audioContext) {
              audioContext.close()
              audioContext = null
            }
          } catch (e) {
            console.error('Error closing audio context:', e)
          }
          
          if (levelAnimationId) {
            cancelAnimationFrame(levelAnimationId)
            levelAnimationId = null
          }
          
          isRecording.value = false
          audioLevel.value = 0
          audioChunks = []
          mediaRecorder = null // 重置mediaRecorder
        }
      }
      
      try {
        mediaRecorder.stop()
        console.log('MediaRecorder stop called')
      } catch (error) {
        console.error('Error stopping mediaRecorder:', error)
        resolve(null)
        
        // 清理资源
        isRecording.value = false
        audioLevel.value = 0
        audioChunks = []
        mediaRecorder = null
      }
    })
  }

  const cancelRecording = () => {
    if (mediaRecorder && isRecording.value) {
      mediaRecorder.stream.getTracks().forEach(track => track.stop())
      if (audioContext) {
        audioContext.close()
        audioContext = null
      }
      if (levelAnimationId) {
        cancelAnimationFrame(levelAnimationId)
        levelAnimationId = null
      }
      isRecording.value = false
      audioLevel.value = 0
      audioChunks = []
    }
  }

  onUnmounted(() => {
    cancelRecording()
  })

  return {
    isRecording,
    audioLevel,
    hasPermission,
    errorMessage,
    requestPermission,
    startRecording,
    stopRecording,
    cancelRecording
  }
}
