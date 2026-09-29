const Svg = ({ children, style }) => (
  <svg className="ti" viewBox="0 0 24 24" style={style}>{children}</svg>
)

export const IconTemp = (p) => (
  <Svg {...p}><path d="M10 13.5a4 4 0 1 0 4 0V5a2 2 0 0 0-4 0v8.5" /><path d="M10 9h4" /></Svg>
)

export const IconHumid = (p) => (
  <Svg {...p}><path d="M12 3l5 6.5a5 5 0 1 1-10 0z" /></Svg>
)

export const IconSun = (p) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="4" />
    <path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M18.4 5.6L17 7M7 17l-1.4 1.4" />
  </Svg>
)

export const IconGear = (p) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="3" />
    <path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M18.4 5.6L17 7M7 17l-1.4 1.4" />
  </Svg>
)

export const IconBulb = (p) => (
  <Svg {...p}><path d="M9 18h6M10 21h4M8.5 14a5 5 0 1 1 7 0l-.5 .5v2h-6v-2z" /></Svg>
)

export const IconFan = (p) => (
  <Svg {...p}>
    <circle cx="12" cy="12" r="2" />
    <path d="M12 10c0-3 1-6 3-6s2 3 0 5M12 14c0 3-1 6-3 6s-2-3 0-5M10 12c-3 0-6-1-6-3s3-2 5 0M14 12c3 0 6 1 6 3s-3 2-5 0" />
  </Svg>
)

export const IconSearch = (p) => (
  <Svg {...p}><circle cx="11" cy="11" r="7" /><path d="M21 21l-4-4" /></Svg>
)

export const IconClock = (p) => (
  <Svg {...p}><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></Svg>
)

export const IconWarn = (p) => (
  <Svg {...p}>
    <path d="M12 9v4M12 17h.01" />
    <path d="M10.3 3.9L2.6 17a2 2 0 0 0 1.7 3h15.4a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" />
  </Svg>
)

export const IconPhoto = (p) => (
  <Svg {...p}>
    <rect x="3" y="5" width="18" height="14" rx="2" /><circle cx="9" cy="11" r="2" />
    <path d="M3 17l5-4 4 3 3-2 6 5" />
  </Svg>
)

export const IconGithub = (p) => (
  <Svg {...p}>
    <path d="M9 19c-4 1.5-4-2.5-6-3m12 5v-3.5c0-1 .1-1.4-.5-2 2.8-.3 5.5-1.4 5.5-6a4.6 4.6 0 0 0-1.3-3.2 4.2 4.2 0 0 0-.1-3.2s-1.1-.3-3.5 1.3a12 12 0 0 0-6 0C7.2 2.9 6.1 3.2 6.1 3.2a4.2 4.2 0 0 0-.1 3.2A4.6 4.6 0 0 0 4.7 9.6c0 4.6 2.7 5.7 5.5 6-.6.6-.6 1.2-.5 2V21" />
  </Svg>
)

export const IconFile = (p) => (
  <Svg {...p}>
    <path d="M14 3v4a1 1 0 0 0 1 1h4" />
    <path d="M17 21H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h7l5 5v11a2 2 0 0 1-2 2z" />
  </Svg>
)

export const IconFigma = (p) => (
  <Svg {...p}>
    <path d="M8 2h4v4H8a2 2 0 0 1 0-4zM12 6h2a2 2 0 0 1 0 4h-2M8 6a2 2 0 0 0 0 4h4M8 10a2 2 0 0 0 0 4h4v-4M12 14a2 2 0 1 0 0 4 2 2 0 0 0 0-4z" />
  </Svg>
)

export const IconCode = (p) => (
  <Svg {...p}><path d="M7 8l-4 4 4 4M17 8l4 4-4 4M14 4l-4 16" /></Svg>
)
