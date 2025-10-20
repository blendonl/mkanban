import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { ParentColor } from '../../core/enums';
import theme from '../theme/colors';

interface ColorPickerProps {
  selectedColor: ParentColor;
  onColorSelect: (color: ParentColor) => void;
}

const COLOR_OPTIONS: Array<{ value: ParentColor; hex: string; label: string }> = [
  { value: ParentColor.RED, hex: theme.parent.red, label: 'Red' },
  { value: ParentColor.ORANGE, hex: theme.parent.orange, label: 'Orange' },
  { value: ParentColor.YELLOW, hex: theme.parent.yellow, label: 'Yellow' },
  { value: ParentColor.GREEN, hex: theme.parent.green, label: 'Green' },
  { value: ParentColor.BLUE, hex: theme.parent.blue, label: 'Blue' },
  { value: ParentColor.CYAN, hex: theme.parent.cyan, label: 'Cyan' },
  { value: ParentColor.PURPLE, hex: theme.parent.purple, label: 'Purple' },
];

export default function ColorPicker({ selectedColor, onColorSelect }: ColorPickerProps) {
  return (
    <View style={styles.container}>
      <Text style={styles.label}>Color</Text>
      <View style={styles.colorGrid}>
        {COLOR_OPTIONS.map((option) => {
          const isSelected = option.value === selectedColor;
          return (
            <TouchableOpacity
              key={option.value}
              style={[
                styles.colorOption,
                { backgroundColor: option.hex },
                isSelected && styles.selectedOption,
              ]}
              onPress={() => onColorSelect(option.value)}
              activeOpacity={0.7}
            >
              {isSelected && <Text style={styles.checkmark}>✓</Text>}
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 16,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
    color: theme.text.primary,
  },
  colorGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  colorOption: {
    width: 50,
    height: 50,
    borderRadius: 25,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 3,
    borderColor: 'transparent',
  },
  selectedOption: {
    borderColor: theme.text.primary,
    transform: [{ scale: 1.1 }],
  },
  checkmark: {
    color: theme.background.primary,
    fontSize: 24,
    fontWeight: 'bold',
  },
});
