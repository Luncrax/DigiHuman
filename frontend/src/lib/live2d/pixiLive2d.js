import * as PIXI from 'pixi.js'
import { Live2DModel } from 'pixi-live2d-display/cubism4'

const CUBISM_CORE_URL =
  '/vendor/live2d/live2dcubismcore.min.js'

const PARAMETER_ID_MAP = {
  angle_x: ['ParamAngleX'],
  angle_y: ['ParamAngleY'],
  angle_z: ['ParamAngleZ'],
  eye_l_open: ['ParamEyeLOpen'],
  eye_r_open: ['ParamEyeROpen'],
  eye_ball_x: ['ParamEyeBallX'],
  eye_ball_y: ['ParamEyeBallY'],
  mouth_open: ['ParamMouthOpenY', 'ParamA'],
  breath: ['ParamBreath'],
}

const MOTION_MAP = {
  idle: { group: 'Idle', index: 0 },
  idle_soft: { group: 'Idle', index: 0 },
  idle_happy: { group: 'Idle', index: 0 },
  idle_sad: { group: 'Idle', index: 1 },
  idle_shy: { group: 'Idle', index: 1 },
  talk: { group: 'TapBody', index: 0 },
  talk_soft: { group: 'TapBody', index: 0 },
  talk_bright: { group: 'TapBody', index: 2 },
  talk_firm: { group: 'TapBody', index: 0 },
  talk_shy: { group: 'TapBody', index: 1 },
  react_sad: { group: 'TapBody', index: 1 },
  react_surprise: { group: 'TapBody', index: 2 },
  react_surprise_big: { group: 'TapBody', index: 3 },
  react_anger: { group: 'TapBody', index: 4 },
  react_anger_strong: { group: 'TapBody', index: 5 },
  react_fear: { group: 'TapBody', index: 1 },
  react_disgust: { group: 'TapBody', index: 4 },
  react_shy: { group: 'TapBody', index: 2 },
  nod: { group: 'TapBody', index: 0 },
  excited: { group: 'TapBody', index: 3 },
  mtn_01: { group: 'Idle', index: 0 },
  sample_01: { group: 'Idle', index: 1 },
  mtn_02: { group: 'TapBody', index: 0 },
  mtn_03: { group: 'TapBody', index: 1 },
  mtn_04: { group: 'TapBody', index: 2 },
  special_01: { group: 'TapBody', index: 3 },
  special_02: { group: 'TapBody', index: 4 },
  special_03: { group: 'TapBody', index: 5 },
}

let cubismCorePromise = null
let tickerRegistered = false

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max)
}

function ensurePixiGlobals() {
  window.PIXI = PIXI

  if (!tickerRegistered) {
    Live2DModel.registerTicker(PIXI.Ticker)
    tickerRegistered = true
  }
}

export function ensureCubismCore() {
  if (window.Live2DCubismCore) {
    return Promise.resolve()
  }

  if (cubismCorePromise) {
    return cubismCorePromise
  }

  cubismCorePromise = new Promise((resolve, reject) => {
    const existing = document.querySelector('script[data-live2d-cubism-core]')

    if (existing) {
      existing.addEventListener('load', () => resolve(), { once: true })
      existing.addEventListener(
        'error',
        () => reject(new Error('Failed to load Cubism Core runtime.')),
        { once: true }
      )
      return
    }

    const script = document.createElement('script')
    script.src = CUBISM_CORE_URL
    script.async = true
    script.dataset.live2dCubismCore = 'true'
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('Failed to load Cubism Core runtime.'))
    document.head.appendChild(script)
  })

  return cubismCorePromise
}

function fitModel(model, width, height, scaleMultiplier = 1) {
  const bounds = model.getLocalBounds()
  const modelWidth = bounds.width || 1
  const modelHeight = bounds.height || 1

  const scale = Math.min(width / modelWidth, height / modelHeight) * scaleMultiplier
  model.scale.set(scale)
  model.anchor.set(0.5, 0.5)
  model.position.set(width * 0.5, height * 0.82)
}

function resolveMotion(motionName) {
  if (!motionName) {
    return MOTION_MAP.idle
  }

  if (MOTION_MAP[motionName]) {
    return MOTION_MAP[motionName]
  }

  const normalized = motionName.toLowerCase()
  return MOTION_MAP[normalized] || MOTION_MAP.idle
}

function setCoreParameter(coreModel, paramId, value) {
  if (!coreModel || typeof coreModel.setParameterValueById !== 'function') {
    return
  }

  try {
    coreModel.setParameterValueById(paramId, value)
  } catch (error) {
    console.warn(`Failed to set Live2D parameter ${paramId}:`, error)
  }
}

function getParameterValueRange(paramId, value) {
  if (paramId === 'ParamA' || paramId === 'ParamMouthOpenY') {
    return clamp(value, 0, 1)
  }

  if (paramId.includes('Angle')) {
    return clamp(value * 30, -30, 30)
  }

  if (paramId.includes('EyeBall')) {
    return clamp(value, -1, 1)
  }

  if (paramId.includes('Eye') || paramId.includes('Breath')) {
    return clamp(value, 0, 1)
  }

  return clamp(value, -1, 1)
}

export async function createPixiLive2d(container, options = {}) {
  if (!container) {
    throw new Error('Live2D container is required.')
  }

  ensurePixiGlobals()
  await ensureCubismCore()

  const {
    modelPath = '/live2d_models/Mao/Mao.model3.json',
    scaleMultiplier = 0.72,
    autoHitMotion = 'TapBody',
  } = options

  container.innerHTML = ''

  const app = new PIXI.Application({
    width: Math.max(container.clientWidth, 1),
    height: Math.max(container.clientHeight, 1),
    backgroundAlpha: 0,
    antialias: true,
    autoStart: true,
    resolution: window.devicePixelRatio || 1,
  })

  app.view.style.width = '100%'
  app.view.style.height = '100%'
  app.view.style.display = 'block'
  app.stage.sortableChildren = true
  container.appendChild(app.view)

  const model = await Live2DModel.from(modelPath)
  model.interactive = true
  model.buttonMode = true
  app.stage.addChild(model)
  fitModel(model, app.renderer.width, app.renderer.height, scaleMultiplier)

  model.on('hit', (hitAreas) => {
    if (hitAreas?.length) {
      model.motion(autoHitMotion).catch((error) => {
        console.warn('Failed to play hit motion:', error)
      })
    }
  })

  const handlePointerMove = (event) => {
    const rect = app.view.getBoundingClientRect()
    const x = event.clientX - rect.left
    const y = event.clientY - rect.top
    model.focus(x, y)
  }

  app.view.addEventListener('pointermove', handlePointerMove)

  const resize = () => {
    const width = Math.max(container.clientWidth, 1)
    const height = Math.max(container.clientHeight, 1)
    app.renderer.resize(width, height)
    fitModel(model, width, height, scaleMultiplier)
  }

  const resizeObserver = new ResizeObserver(() => resize())
  resizeObserver.observe(container)

  const playMotion = async (motionName) => {
    const target = resolveMotion(motionName)
    return model.motion(target.group, target.index)
  }

  const setExpression = async (expressionName) => {
    const expression = expressionName || 'exp_01'
    return model.expression(expression)
  }

  const updateParameters = (parameters = {}) => {
    const coreModel = model.internalModel?.coreModel

    Object.entries(parameters).forEach(([key, rawValue]) => {
      const aliases = PARAMETER_ID_MAP[key]
      if (!aliases) {
        return
      }

      const value = Number(rawValue)
      if (Number.isNaN(value)) {
        return
      }

      aliases.forEach((paramId) => {
        setCoreParameter(coreModel, paramId, getParameterValueRange(paramId, value))
      })
    })
  }

  const destroy = () => {
    resizeObserver.disconnect()
    app.view.removeEventListener('pointermove', handlePointerMove)
    model.removeAllListeners?.()
    model.destroy?.({ children: true })
    app.destroy(true, { children: true, texture: true, baseTexture: true })
    container.innerHTML = ''
  }

  return {
    app,
    model,
    resize,
    destroy,
    playMotion,
    setExpression,
    updateParameters,
  }
}
