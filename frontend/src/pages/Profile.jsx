import { useEffect, useState } from 'react'

import { api } from '../api'
import { IconCode, IconFigma, IconFile, IconGithub, IconPhoto, IconWarn } from '../components/Icons'

// UC 5.2.5 - Xem profile, lấy dữ liệu từ GET api/users/me.
export default function Profile() {
  const [user, setUser] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.me().then(setUser).catch((err) => setError(err.message))
  }, [])

  if (error) {
    return (
      <div className="banner">
        <IconWarn style={{ fontSize: 18 }} />
        Không lấy được thông tin tài khoản: {error}
      </div>
    )
  }
  if (!user) return <div className="empty">Đang tải…</div>

  return (
    <div className="prof">
      <div className="card" style={{ padding: 20 }}>
        <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 18 }}>Sinh viên thực hiện</div>
        <div style={{ display: 'flex', gap: 22, alignItems: 'flex-start' }}>
          <div className="avatar">
            <IconPhoto style={{ fontSize: 26 }} />
            <span style={{ fontSize: 12 }}>Ảnh đại diện</span>
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div className="row"><span className="k">Tên đăng nhập</span><span className="v mono">{user.username}</span></div>
            <div className="row"><span className="k">Họ và tên</span><span className="v">{user.full_name}</span></div>
            <div className="row"><span className="k">Mã sinh viên</span><span className="v mono">{user.student_id}</span></div>
            <div className="row"><span className="k">Lớp</span><span className="v">{user.class}</span></div>
            <div className="row"><span className="k">Học phần</span><span className="v">IoT và Ứng dụng</span></div>
            <div className="row"><span className="k">Giảng viên</span><span className="v">TS. Nguyễn Quốc Uy</span></div>
          </div>
        </div>
      </div>

      <div className="card" style={{ padding: 20, alignSelf: 'start' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
          <span style={{ fontSize: 16, fontWeight: 600 }}>Sản phẩm bàn giao</span>
          <span style={{ fontSize: 12, color: 'var(--text3)' }}>4 liên kết</span>
        </div>

        <a className="link" href="https://github.com" target="_blank" rel="noreferrer">
          <IconGithub style={{ fontSize: 22 }} />
          <div><div className="lt">Mã nguồn</div><div className="ls">github.com/…</div></div>
        </a>

        <div className="link">
          <IconFile style={{ fontSize: 22, color: 'var(--blue)' }} />
          <div><div className="lt">Báo cáo PDF</div><div className="ls">BaoCao.pdf</div></div>
        </div>

        <a
          className="link"
          href="https://www.figma.com/design/vUM4DOg1pnHJ1FEVp8U3s2/Untitled?node-id=0-1&t=YWQgz7rud9UP4f5B-1"
          target="_blank"
          rel="noreferrer"
        >
          <IconFigma style={{ fontSize: 22 }} />
          <div><div className="lt">Thiết kế Figma</div><div className="ls">figma.com/design/vUM4DOg1…</div></div>
        </a>

        <a className="link" href="http://localhost:8000/docs" target="_blank" rel="noreferrer">
          <IconCode style={{ fontSize: 22, color: 'var(--green)' }} />
          <div><div className="lt">Tài liệu API</div><div className="ls">/docs (Swagger UI)</div></div>
        </a>
      </div>
    </div>
  )
}
