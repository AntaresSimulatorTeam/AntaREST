export function useAppMode() {
  const isDesktopMode = import.meta.env.MODE === "desktop";
  const isWebMode = !isDesktopMode;

  return {
    isDesktopMode,
    isWebMode,
  };
}
