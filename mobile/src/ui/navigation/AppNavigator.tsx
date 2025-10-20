import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';

// Import screens
import BoardListScreen from '../screens/BoardListScreen';
import BoardScreen from '../screens/BoardScreen';
import ItemDetailScreen from '../screens/ItemDetailScreen';
import SettingsScreen from '../screens/SettingsScreen';
import theme from '../theme/colors';

// Define navigation types
// Note: Pass only IDs, not full objects, to avoid serialization warnings
export type RootStackParamList = {
  BoardList: undefined;
  Board: { boardId: string };
  ItemDetail: { boardId: string; itemId?: string; columnId?: string };
  Settings: undefined;
};

const Stack = createStackNavigator<RootStackParamList>();

export default function AppNavigator() {
  return (
    <NavigationContainer>
      <Stack.Navigator
        initialRouteName="BoardList"
        screenOptions={{
          headerStyle: {
            backgroundColor: theme.header.background,
          },
          headerTintColor: theme.header.text,
          headerTitleStyle: {
            fontWeight: 'bold',
          },
        }}
      >
        <Stack.Screen
          name="BoardList"
          component={BoardListScreen}
          options={{
            title: 'My Boards',
          }}
        />
        <Stack.Screen
          name="Board"
          component={BoardScreen}
          options={{
            title: 'Board',
          }}
        />
        <Stack.Screen
          name="ItemDetail"
          component={ItemDetailScreen}
          options={{
            title: 'Item Details',
            presentation: 'modal',
          }}
        />
        <Stack.Screen
          name="Settings"
          component={SettingsScreen}
          options={{
            title: 'Settings',
          }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
