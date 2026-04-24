import { ref, onUnmounted } from 'vue'

export function useAudioPlayer() {
  const isPlaying = ref(false)
  const isLoading = ref(false)
  const currentAudio = ref(null)
  const errorMessage = ref('')

  const playBase64Audio = (base64Audio, audioFormat = 'audio/mpeg') => {
    return new Promise((resolve, reject) => {
      try {
        if (currentAudio.value) {
          currentAudio.value.pause()
          currentAudio.value = null
        }

        const audio = new Audio()
        currentAudio.value = audio
        
        const audioBlob = base64ToBlob(base64Audio, audioFormat)
        const audioUrl = URL.createObjectURL(audioBlob)
        
        audio.src = audioUrl
        audio.preload = 'auto'

        audio.onloadstart = () => {
          isLoading.value = true
          errorMessage.value = ''
        }

        audio.oncanplay = () => {
          isLoading.value = false
        }

        audio.onplay = () => {
          isPlaying.value = true
        }

        audio.onended = () => {
          isPlaying.value = false
          URL.revokeObjectURL(audioUrl)
          resolve()
        }

        audio.onerror = (error) => {
          isPlaying.value = false
          isLoading.value = false
          errorMessage.value = '音频播放失败'
          console.error('Audio playback error:', error)
          reject(error)
        }

        audio.play().catch(error => {
          isPlaying.value = false
          isLoading.value = false
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
        if (currentAudio.value) {
          currentAudio.value.pause()
          currentAudio.value = null
        }

        const audio = new Audio(audioUrl)
        currentAudio.value = audio
        audio.preload = 'auto'

        audio.onplay = () => {
          isPlaying.value = true
          isLoading.value = false
        }

        audio.onended = () => {
          isPlaying.value = false
          resolve()
        }

        audio.onerror = (error) => {
          isPlaying.value = false
          isLoading.value = false
          errorMessage.value = '音频播放失败'
          reject(error)
        }

        audio.onloadstart = () => {
          isLoading.value = true
        }

        audio.play().catch(error => {
          isPlaying.value = false
          isLoading.value = false
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
    if (currentAudio.value) {
      currentAudio.value.pause()
      currentAudio.value.currentTime = 0
      currentAudio.value = null
    }
    isPlaying.value = false
    isLoading.value = false
  }

  const base64ToBlob = (base64, mimeType) => {
    const byteCharacters = atob(base64)
    const byteNumbers = new Array(byteCharacters.length)
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i)
    }
    const byteArray = new Uint8Array(byteNumbers)
    return new Blob([byteArray], { type: mimeType })
  }

  onUnmounted(() => {
    stopPlayback()
  })

  return {
    isPlaying,
    isLoading,
    errorMessage,
    playBase64Audio,
    playAudioFromUrl,
    stopPlayback
  }
}