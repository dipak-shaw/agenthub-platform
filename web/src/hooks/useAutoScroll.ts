import { useEffect, useRef, useState } from "react";
export function useAutoScroll(change: unknown) {
  const ref = useRef<HTMLDivElement>(null);
  const [away, setAway] = useState(false);
  useEffect(() => {
    if (!away && ref.current) ref.current.scrollTop = ref.current.scrollHeight;
  }, [change, away]);
  return {
    ref,
    away,
    onScroll: () => {
      const el = ref.current;
      if (el) setAway(el.scrollHeight - el.scrollTop - el.clientHeight > 100);
    },
    jump: () => {
      setAway(false);
      ref.current?.scrollTo({
        top: ref.current.scrollHeight,
        behavior: "smooth",
      });
    },
  };
}
