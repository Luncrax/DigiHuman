import { onUnmounted, ref } from 'vue'

export function useAudioPlayer() {
  const isPlaying = ref(false)
  const isLoading = ref(false)
  const currentAudio = ref(null)
  const errorMessage = ref('')
  const capabilityWarning = ref('')

  let audioContext = null
  let analyser = null
  let sourceNode = null
  let animationFrame = null
  let analyserBuffer = null
  let currentObjectUrl = null

  const dispatchLipSync = (mouthOpen = 0) => {
    window.dispatchEvent(
      new CustomEvent('digihuman-live2d-lipsync', {
        detail: { mouth_open: mouthOpen },
      })
    )
  }

  const stopLipSyncLoop = () => {
    if (animationFrame) {
      cancelAnimationFrame(animationFrame)
      animationFrame = null
    }
    dispatchLipSync(0)
  }

  const cleanupAudioGraph = () => {
    stopLipSyncLoop()

    if (sourceNode) {
      try {
        sourceNode.disconnect()
      } catch (error) {
        console.warn('Failed to disconnect audio source node:', error)
      }
      sourceNode = null
    }

    if (analyser) {
      try {
        analyser.disconnect()
      } catch (error) {
        console.warn('Failed to disconnect audio analyser:', error)
      }
      analyser = null
    }
  }

  const revokeCurrentObjectUrl = () => {
    if (!currentObjectUrl) {
      return
    }

    try {
      URL.revokeObjectURL(currentObjectUrl)
    } catch (error) {
      console.warn('Failed to revoke audio object URL:', error)
    }

    currentObjectUrl = null
  }

  const releaseCurrentAudio = () => {
    if (!currentAudio.value) {
      return
    }

    try {
      currentAudio.value.pause()
      currentAudio.value.removeAttribute('src')
      currentAudio.value.load?.()
    } catch (error) {
      console.warn('Failed to release current audio element:', error)
    }

    currentAudio.value = null
  }

  const ensureAudioContext = async () => {
    if (!audioContext) {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext
      if (!AudioContextClass) {
        capabilityWarning.value = '当前浏览器不支持实时嘴型同步，已自动降级为普通音频播放。'
        return null
      }
      audioContext = new AudioContextClass()
    }

    if (audioContext.state === 'suspended') {
      await audioContext.resume()
    }

    return audioContext
  }

  const primeAudio = async () => {
    errorMessage.value = ''

    try {
      const ctx = await ensureAudioContext()
      if (!ctx) {
        return false
      }
      capabilityWarning.value = ''
      return true
    } catch (error) {
      capabilityWarning.value = '浏览器阻止了音频初始化，请先点击页面后再试一次。'
      console.warn('Audio priming failed:', error)
      return false
    }
  }

  const startLipSyncLoop = (audio) => {
    if (!analyser || !audio) {
      return
    }

    analyserBuffer = analyserBuffer || new Uint8Array(analyser.fftSize)

    const tick = () => {
      if (!analyser || audio.paused || audio.ended) {
        dispatchLipSync(0)
        animationFrame = null
        return
      }

      analyser.getByteTimeDomainData(analyserBuffer)

      let sumSquares = 0
      for (let i = 0; i < analyserBuffer.length; i += 1) {
        const centered = (analyserBuffer[i] - 128) / 128
        sumSquares += centered * centered
      }

      const rms = Math.sqrt(sumSquares / analyserBuffer.length)
      const mouthOpen = Math.min(0.95, Math.max(0, (rms - 0.015) * 6.5))
      dispatchLipSync(mouthOpen)
      animationFrame = requestAnimationFrame(tick)
    }

    stopLipSyncLoop()
    animationFrame = requestAnimationFrame(tick)
  }

  const setupAudioAnalysis = async (audio) => {
    const ctx = await ensureAudioContext()
    if (!ctx || !audio) {
      return
    }

    try {
      cleanupAudioGraph()

      analyser = ctx.createAnalyser()
      analyser.fftSize = 2048
      analyser.smoothingTimeConstant = 0.55
      sourceNode = ctx.createMediaElementSource(audio)
      sourceNode.connect(analyser)
      analyser.connect(ctx.destination)
      capabilityWarning.value = ''
      startLipSyncLoop(audio)
    } catch (error) {
      capabilityWarning.value = '实时嘴型同步初始化失败，已自动降级为基础说话状态。'
      cleanupAudioGraph()
      throw error
    }
  }

  const base64ToBlob = (base64, mimeType) => {
    const normalized = String(base64 || '').trim()
    const byteCharacters = atob(normalized)
    const byteNumbers = new Array(byteCharacters.length)
    for (let i = 0; i < byteCharacters.length; i += 1) {
      byteNumbers[i] = byteCharacters.charCodeAt(i)
    }
    const byteArray = new Uint8Array(byteNumbers)
    return new Blob([byteArray], { type: mimeType })
  }

  const bindAudioLifecycle = (audio, cleanup) => {
    audio.onloadstart = () => {
      isLoading.value = true
      errorMessage.value = ''
    }

    audio.oncanplay = () => {
      isLoading.value = false
    }

    audio.onplay = () => {
      isPlaying.value = true
      setupAudioAnalysis(audio).catch((error) => {
        capabilityWarning.value = '音频能量分析未启用，嘴型将使用基础说话状态。'
        console.warn('Audio analysis setup failed:', error)
      })
    }

    audio.onended = () => {
      isPlaying.value = false
      isLoading.value = false
      cleanupAudioGraph()
      cleanup?.()
    }

    audio.onerror = (error) => {
      isPlaying.value = false
      isLoading.value = false
      cleanupAudioGraph()
      errorMessage.value = '音频播放失败'
      console.error('Audio playback error:', error)
      cleanup?.()
    }
  }

  const playBase64Audio = (base64Audio, audioFormat = 'audio/mpeg') => {
    return new Promise((resolve, reject) => {
      try {
        releaseCurrentAudio()
        cleanupAudioGraph()
        revokeCurrentObjectUrl()

        const audio = new Audio()
        currentAudio.value = audio

        const audioBlob = base64ToBlob(base64Audio, audioFormat)
        const audioUrl = URL.createObjectURL(audioBlob)
        currentObjectUrl = audioUrl
        audio.src = audioUrl
        audio.preload = 'auto'

        bindAudioLifecycle(audio, () => {
          if (currentAudio.value === audio) {
            currentAudio.value = null
          }
          if (currentObjectUrl === audioUrl) {
            revokeCurrentObjectUrl()
          }
          resolve()
        })

        audio.play().catch((error) => {
          isPlaying.value = false
          isLoading.value = false
          cleanupAudioGraph()
          if (currentAudio.value === audio) {
            currentAudio.value = null
          }
          if (currentObjectUrl === audioUrl) {
            revokeCurrentObjectUrl()
          }
          errorMessage.value = error.message || '播放失败'
          reject(error)
        })
      } catch (error) {
        errorMessage.value = error.message || '音频处理失败'
        reject(error)
      }
    })
  }

  const playAudioFromUrl = (audioUrl) => {
    return new Promise((resolve, reject) => {
      try {
        releaseCurrentAudio()
        cleanupAudioGraph()
        revokeCurrentObjectUrl()

        const audio = new Audio(audioUrl)
        currentAudio.value = audio
        audio.preload = 'auto'

        bindAudioLifecycle(audio, () => {
          if (currentAudio.value === audio) {
            currentAudio.value = null
          }
          resolve()
        })

        audio.play().catch((error) => {
          isPlaying.value = false
          isLoading.value = false
          cleanupAudioGraph()
          if (currentAudio.value === audio) {
            currentAudio.value = null
          }
          errorMessage.value = error.message || '播放失败'
          reject(error)
        })
      } catch (error) {
        errorMessage.value = error.message || '音频处理失败'
        reject(error)
      }
    })
  }

  const stopPlayback = () => {
    releaseCurrentAudio()
    cleanupAudioGraph()
    revokeCurrentObjectUrl()
    isPlaying.value = false
    isLoading.value = false
  }

  onUnmounted(() => {
    stopPlayback()
    if (audioContext && audioContext.state !== 'closed') {
      audioContext.close().catch(() => {})
    }
  })

  return {
    isPlaying,
    isLoading,
    errorMessage,
    capabilityWarning,
    primeAudio,
    playBase64Audio,
    playAudioFromUrl,
    stopPlayback,
  }
}
