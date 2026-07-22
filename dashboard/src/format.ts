export function percent(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "percent",
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(value);
}

export function integer(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}

export function bytes(value: number): string {
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / 1024 / 1024).toFixed(1)} MB`;
}

export function titleCase(value: string): string {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function shortHash(value: string, size = 12): string {
  const hash = value.includes(":") ? value.split(":").at(-1) ?? value : value;
  return hash.length > size ? `${hash.slice(0, size)}…` : hash;
}

