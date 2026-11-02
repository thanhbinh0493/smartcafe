import { describe, expect, it } from 'vitest'
import { formatVND, normalizeText } from './format'

describe('F1-FE-01 formatVND (NFR-U4)', () => {
  it.each([
    [0, '0đ'],
    [500, '500đ'],
    [45000, '45.000đ'],
    [33600, '33.600đ'],
    [1234567, '1.234.567đ'],
  ])('%i -> %s', (n, s) => expect(formatVND(n)).toBe(s))
})

describe('F1-FE-02 normalizeText (tìm không dấu)', () => {
  it('bỏ dấu, đ -> d, chữ thường', () => {
    expect(normalizeText('Cà Phê Sữa Đá')).toBe('ca phe sua da')
    expect(normalizeText('  Trà đào  ')).toBe('tra dao')
  })
})
