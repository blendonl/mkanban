import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { ParentColor } from '../../core/enums';

interface ColorPickerProps {
  selectedColor: ParentColor;
  onColorSelect: (color: ParentColor) => void;
}

const COLOR_OPTIONS: Array<{ value: ParentColor; hex: string; label: string }> = [
  { value: ParentColor.RED, hex: '#ef4444', label: 'Red' },
  { value: ParentColor.ORANGE, hex: '#f97316', label: 'Orange' },
  { value: ParentColor.YELLOW, hex: '#eab308', label: 'Yellow' },
  { value: ParentColor.GREEN, hex: '#22c55e', label: 'Green' },
  { value: ParentColor.BLUE, hex: '#3b82f6', label: 'Blue' },
  { value: ParentColor.CYAN, hex: '#06b6d4', label: 'Cyan' },
  { value: ParentColor.PURPLE, hex: '#a855f7', label: 'Purple' },
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
    color: '#1f2937',
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
    borderColor: '#1f2937',
    transform: [{ scale: 1.1 }],
  },
  checkmark: {
    color: '#fff',
    fontSize: 24,
    fontWeight: 'bold',
  },
});
