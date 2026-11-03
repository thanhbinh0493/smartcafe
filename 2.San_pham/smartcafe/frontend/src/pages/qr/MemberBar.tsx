import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import type { ApiError } from '../../api/client'
import { getMe } from '../../api/customer'
import { isSessionError, POINT_VALUE_VND, useMember } from '../../auth/MemberContext'
import { formatVND } from '../../lib/format'

/** Dòng trạng thái khách trên W01 (UC07): thành viên thấy lời chào + điểm + nút Thoát;
 *  khách ẩn danh thấy nút "Nhập SĐT tích điểm" (UC01 – quy tắc). */
export default function MemberBar() {
  const { member, expired, logout, expire, setPoints } = useMember()
  const token = member?.token

  // Cập nhật số điểm mới nhất (VD: vừa được cộng điểm ở đơn trước) mỗi lần mở menu
  useEffect(() => {
    if (!token) return
    let alive = true
    getMe(token)
      .then((me) => alive && setPoints(me.loyalty_points))
      .catch((e: ApiError) => alive && isSessionError(e.code, e.status) && expire())
    return () => {
      alive = false
    }
  }, [token, setPoints, expire])

  if (member) {
    return (
      <div className="flex items-center justify-between gap-2 bg-white px-4 py-2 text-sm" data-testid="member-bar">
        <span>
          Xin chào{member.name ? `, ${member.name}` : ''} –{' '}
          <b className="text-coffee">{member.points} điểm</b>{' '}
          <span className="text-stone-500">(≈ {formatVND(member.points * POINT_VALUE_VND)})</span>
        </span>
        <button onClick={logout} className="shrink-0 rounded-full border border-stone-300 px-3 py-1 text-stone-600">
          Thoát
        </button>
      </div>
    )
  }
  return (
    <div className="bg-white px-4 py-2 text-sm">
      {expired && (
        <p role="status" className="mb-1 text-amber-700">
          Phiên thành viên đã hết hạn, bạn đang gọi món ở chế độ khách vãng lai.
        </p>
      )}
      <div className="flex items-center justify-between gap-2">
        <span className="text-stone-600">Khách vãng lai</span>
        <Link to="../otp" relative="path" className="rounded-full border border-coffee px-3 py-1 font-medium text-coffee">
          Nhập SĐT tích điểm
        </Link>
      </div>
    </div>
  )
}
