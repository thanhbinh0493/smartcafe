import { describe, expect, it, vi } from 'vitest'

class FakeAudioContext {
  static created = 0
  currentTime = 1
  destination = {}
  resume = vi.fn(async () => {})
  osc = { frequency: { value: 0 }, connect: vi.fn(), start: vi.fn(), stop: vi.fn() }
  createOscillator = () => this.osc
  createGain = () => ({ gain: { value: 0 }, connect: vi.fn() })
  constructor() {
    FakeAudioContext.created++
    last = this
  }
}
let last: FakeAudioContext

describe('F3-FE-15 âm báo món mới (Web Audio)', () => {
  it('phát tiếng bíp 0,25 giây; dùng chung 1 AudioContext; trình duyệt không hỗ trợ thì bỏ qua, không lỗi', async () => {
    vi.resetModules()
    vi.stubGlobal('AudioContext', FakeAudioContext)
    const { playBeep, unlockAudio } = await import('./beep')
    unlockAudio()
    expect(last.resume).toHaveBeenCalled()
    playBeep()
    expect(last.osc.frequency.value).toBe(880)
    expect(last.osc.start).toHaveBeenCalled()
    expect(last.osc.stop).toHaveBeenCalledWith(1.25)
    expect(FakeAudioContext.created).toBe(1)

    vi.resetModules()
    vi.stubGlobal('AudioContext', undefined)
    const fresh = await import('./beep')
    expect(() => {
      fresh.unlockAudio()
      fresh.playBeep()
    }).not.toThrow()

    vi.resetModules()
    vi.stubGlobal('AudioContext', function Broken() {
      throw new Error('blocked')
    })
    const broken = await import('./beep')
    expect(() => {
      broken.unlockAudio()
      broken.playBeep()
    }).not.toThrow()
  })
})
