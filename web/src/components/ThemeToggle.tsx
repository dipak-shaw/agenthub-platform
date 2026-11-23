import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";
export default function ThemeToggle() {
  const [dark, setDark] = useState(() =>
    localStorage.getItem("theme")
      ? localStorage.getItem("theme") === "dark"
      : matchMedia("(prefers-color-scheme: dark)").matches,
  );
  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("theme", dark ? "dark" : "light");
  }, [dark]);
  return (
    <button
      className="icon-button"
      aria-label={dark ? "Use light theme" : "Use dark theme"}
      onClick={() => setDark(!dark)}
    >
      {dark ? <Sun size={18} /> : <Moon size={18} />}
    </button>
  );
}
