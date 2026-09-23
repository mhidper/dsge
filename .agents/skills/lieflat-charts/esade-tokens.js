/**
 * Tokens de diseño y utilidades de renderizado para Lieflat Charts
 * Adaptado a la Identidad Visual Oficial de EsadeEcPol (Center for Economic Policy)
 */

export const ESADE_TOKENS = {
  colors: {
    primary: '#000b3d',       // Deep Navy
    secondary: '#0e1e63',     // Midnight Navy
    royalBlue: '#1e4192',     // Royal Blue (acento institucional)
    coral: '#ff5a5f',         // Coral (alerta / inflación)
    slateBlue: '#505b8c',     // Slate Blue (secundario)
    iceBlue: '#eef2ff',       // Ice Blue (fondos de realce)
    iceBlueBand: 'rgba(30, 65, 146, 0.12)', // Banda 80% IC
    iceBlueBandDeep: 'rgba(30, 65, 146, 0.22)', // Banda 50% IC
    border: '#e2e8f0',        // Slate Border
    bgCard: '#f8fafc',        // Off-white soft
    bgPage: '#ffffff',        // Blanco puro
    positive: '#16a34a',      // Verde favorable
    warning: '#f59e0b',       // Ámbar
    textDark: '#161616',      // Titulares y cifras
    textBody: '#334155',      // Cuerpo de texto
    textMuted: '#767d8a',     // Metadatos y fuentes
    gridLine: 'rgba(226, 232, 240, 0.8)',
    hairline: 'rgba(118, 125, 138, 0.35)'
  },
  fonts: {
    display: 'Georgia, "Times New Roman", serif',
    sans: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    mono: 'ui-monospace, "SF Mono", Menlo, Consolas, monospace'
  },
  radii: {
    card: '16px',
    pill: '9999px',
    small: '6px'
  },
  transitions: {
    fast: '0.2s cubic-bezier(0.16, 1, 0.3, 1)',
    normal: '0.35s cubic-bezier(0.16, 1, 0.3, 1)'
  }
};

/**
 * Formateador de números con reglas oficiales de EsadeEcPol
 */
export function formatEsadeNumber(value, type = 'rate') {
  if (value === null || value === undefined || isNaN(value)) return '—';
  
  if (type === 'gdp' || type === 'growth') {
    // Exactamente 1 decimal
    return value.toLocaleString('es-ES', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + '%';
  } else if (type === 'rate' || type === 'cpi' || type === 'unemployment' || type === 'interest') {
    // 2 decimales
    return value.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + '%';
  } else {
    return value.toLocaleString('es-ES', { minimumFractionDigits: 1, maximumFractionDigits: 2 });
  }
}
