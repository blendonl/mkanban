/**
 * Catppuccin Mocha Theme with Pure Black Background
 * https://github.com/catppuccin/catppuccin
 */

export const CatppuccinColors = {
  // Base colors - using pure black for background
  base: '#000000',        // Pure black background instead of #1e1e2e
  mantle: '#181825',
  crust: '#11111b',

  // Surface colors
  surface0: '#313244',
  surface1: '#45475a',
  surface2: '#585b70',

  // Overlay colors
  overlay0: '#6c7086',
  overlay1: '#7f849c',
  overlay2: '#9399b2',

  // Text colors
  text: '#cdd6f4',
  subtext0: '#a6adc8',
  subtext1: '#bac2de',

  // Accent colors
  blue: '#89b4fa',
  lavender: '#b4befe',
  sapphire: '#74c7ec',
  sky: '#89dceb',
  teal: '#94e2d5',
  green: '#a6e3a1',
  yellow: '#f9e2af',
  peach: '#fab387',
  maroon: '#eba0ac',
  red: '#f38ba8',
  mauve: '#cba6f7',
  pink: '#f5c2e7',
  flamingo: '#f2cdcd',
  rosewater: '#f5e0dc',
};

// Semantic color mappings for easier usage
export const theme = {
  // Background colors
  background: {
    primary: CatppuccinColors.base,
    secondary: CatppuccinColors.mantle,
    tertiary: CatppuccinColors.crust,
    elevated: CatppuccinColors.surface0,
    elevatedHigh: CatppuccinColors.surface1,
  },

  // Text colors
  text: {
    primary: CatppuccinColors.text,
    secondary: CatppuccinColors.subtext1,
    tertiary: CatppuccinColors.subtext0,
    muted: CatppuccinColors.overlay2,
    disabled: CatppuccinColors.overlay1,
  },

  // Border colors
  border: {
    primary: CatppuccinColors.surface0,
    secondary: CatppuccinColors.surface1,
    focus: CatppuccinColors.blue,
  },

  // Accent colors for interactive elements
  accent: {
    primary: CatppuccinColors.blue,
    secondary: CatppuccinColors.lavender,
    success: CatppuccinColors.green,
    warning: CatppuccinColors.yellow,
    error: CatppuccinColors.red,
    info: CatppuccinColors.sapphire,
  },

  // Parent/tag colors (matching the existing ParentColor enum)
  parent: {
    red: CatppuccinColors.red,
    orange: CatppuccinColors.peach,
    yellow: CatppuccinColors.yellow,
    green: CatppuccinColors.green,
    blue: CatppuccinColors.blue,
    cyan: CatppuccinColors.sky,
    purple: CatppuccinColors.mauve,
  },

  // Card colors
  card: {
    background: CatppuccinColors.surface0,
    backgroundHover: CatppuccinColors.surface1,
    border: CatppuccinColors.surface1,
    shadow: '#000000',
  },

  // Input colors
  input: {
    background: CatppuccinColors.surface0,
    backgroundFocus: CatppuccinColors.surface1,
    border: CatppuccinColors.surface1,
    borderFocus: CatppuccinColors.blue,
    text: CatppuccinColors.text,
    placeholder: CatppuccinColors.overlay2,
  },

  // Button colors
  button: {
    primary: {
      background: CatppuccinColors.blue,
      text: CatppuccinColors.base,
    },
    secondary: {
      background: CatppuccinColors.surface1,
      text: CatppuccinColors.text,
    },
    danger: {
      background: CatppuccinColors.red,
      text: CatppuccinColors.base,
    },
    success: {
      background: CatppuccinColors.green,
      text: CatppuccinColors.base,
    },
  },

  // Badge colors
  badge: {
    background: CatppuccinColors.blue,
    text: CatppuccinColors.base,
  },

  // Header/navigation colors
  header: {
    background: CatppuccinColors.blue,
    text: CatppuccinColors.base,
  },

  // Modal/overlay colors
  modal: {
    background: CatppuccinColors.mantle,
    overlay: 'rgba(0, 0, 0, 0.7)',
  },
};

export default theme;
