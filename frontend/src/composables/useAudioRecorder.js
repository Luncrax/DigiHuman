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
          
          const arrayBuffer = await audioBlob.arrayBuffer()
          console.log('Array buffer length:', arrayBuffer.byteLength)
          
          if (arrayBuffer.byteLength === 0) {
            console.error('Array buffer is empty')
            resolve(null)
            return
          }
          
          const base64 = arrayBufferToBase64(arrayBuffer)
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

  const arrayBufferToBase64 = (buffer) => {
    let binary = ''
    const bytes = new Uint8Array(buffer)
    const len = bytes.byteLength
    for (let i = 0; i < len; i++) {
      binary += String.fromCharCode(bytes[i])
    }
    return btoa(binary)
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