import { registerRootComponent } from 'expo';
import { Buffer } from 'buffer';

// Polyfill Buffer for React Native (needed by gray-matter)
(global as any).Buffer = Buffer;

import App from './App';

// registerRootComponent calls AppRegistry.registerComponent('main', () => App);
// It also ensures that whether you load the app in Expo Go or in a native build,
// the environment is set up appropriately
registerRootComponent(App);
