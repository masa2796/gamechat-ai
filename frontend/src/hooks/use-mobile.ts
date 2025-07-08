import * as React from "react"

const MOBILE_BREAKPOINT = 768

export function useIsMobile() {
  const [isMobile, setIsMobile] = React.useState<boolean>(false)

  React.useEffect(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
      setIsMobile(false)
      return
    }
    let mql: MediaQueryList | null = null
    try {
      mql = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`)
      const onChange = () => {
        setIsMobile(window.innerWidth < MOBILE_BREAKPOINT)
      }
      try {
        mql.addEventListener("change", onChange)
      } catch {
        // addEventListenerが失敗しても無視
      }
      setIsMobile(window.innerWidth < MOBILE_BREAKPOINT)
      return () => {
        try {
          if (mql) mql.removeEventListener("change", onChange)
        } catch {
          // removeEventListenerが失敗しても無視
        }
      }
    } catch {
      setIsMobile(false)
    }
  }, [])

  return !!isMobile
}
