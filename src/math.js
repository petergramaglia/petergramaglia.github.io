export const clamp = (value, min = 0, max = 1) => Math.min(max, Math.max(min, value));
export function follow(current, target, seconds) {
  return current + (target - current) * (1 - Math.exp(-12 * Math.max(0, seconds)));
}
export function bufferSize(width, height, dpr, limit = 2_500_000, maxAxis = 8192) {
  const ratio = Math.min(dpr, 1.5, Math.sqrt(limit / (width * height)), maxAxis / width, maxAxis / height);
  return [Math.max(1, Math.floor(width * ratio)), Math.max(1, Math.floor(height * ratio))];
}
