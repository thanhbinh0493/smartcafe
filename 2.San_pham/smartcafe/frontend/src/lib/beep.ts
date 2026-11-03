/** Âm báo khi có món mới trên màn hình Bar (UC17). Dùng Web Audio, không cần file âm thanh.
 *  Trình duyệt chỉ cho phát âm thanh sau khi người dùng đã bấm vào trang ít nhất 1 lần, nên màn hình Bar
 *  gọi `unlockAudio()` ở lần bấm đầu tiên. */
let ctx: AudioContext | null = null

function audio(): AudioContext | null {
  const AC = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
  if (!AC) return null
  ctx ??= new AC()
  return ctx
}

export function unlockAudio(): void {
  try {
    void audio()?.resume()
  } catch {
    /* trình duyệt không hỗ trợ: bỏ qua */
  }
}

export function playBeep(): void {
  try {
    const ac = audio()
    if (!ac) return
    const osc = ac.createOscillator()
    const gain = ac.createGain()
    osc.frequency.value = 880
    gain.gain.value = 0.2
    osc.connect(gain)
    gain.connect(ac.destination)
    osc.start()
    osc.stop(ac.currentTime + 0.25)
  } catch {
    /* không phát được âm thanh thì vẫn có thông báo trên màn hình */
  }
}
