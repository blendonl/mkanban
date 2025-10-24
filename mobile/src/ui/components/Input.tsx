/**
 * Input Components
 * Reusable input components with consistent styling
 */

import React, { forwardRef } from 'react';
import {
  TextInput,
  View,
  Text,
  StyleSheet,
  TextInputProps,
  ViewStyle,
} from 'react-native';
import theme from '../theme';

export interface InputProps extends TextInputProps {
  label?: string;
  error?: string;
  hint?: string;
  containerStyle?: ViewStyle;
  required?: boolean;
}

/**
 * Base Input Component
 */
export const Input = forwardRef<TextInput, InputProps>(
  (
    {
      label,
      error,
      hint,
      containerStyle,
      required = false,
      style,
      ...props
    },
    ref
  ) => {
    return (
      <View style={[styles.container, containerStyle]}>
        {label && (
          <Text style={styles.label}>
            {label}
            {required && <Text style={styles.required}> *</Text>}
          </Text>
        )}
        <TextInput
          ref={ref}
          style={[
            styles.input,
            error && styles.inputError,
            style,
          ]}
          placeholderTextColor={theme.input.placeholder}
          {...props}
        />
        {error && <Text style={styles.errorText}>{error}</Text>}
        {hint && !error && <Text style={styles.hintText}>{hint}</Text>}
      </View>
    );
  }
);

Input.displayName = 'Input';

/**
 * TextArea Component (multiline input)
 */
export interface TextAreaProps extends InputProps {
  numberOfLines?: number;
  minHeight?: number;
}

export const TextArea = forwardRef<TextInput, TextAreaProps>(
  (
    {
      label,
      error,
      hint,
      containerStyle,
      required = false,
      numberOfLines = 4,
      minHeight,
      style,
      ...props
    },
    ref
  ) => {
    const textAreaHeight = minHeight || numberOfLines * 20 + theme.spacing.inputPadding.vertical * 2;

    return (
      <View style={[styles.container, containerStyle]}>
        {label && (
          <Text style={styles.label}>
            {label}
            {required && <Text style={styles.required}> *</Text>}
          </Text>
        )}
        <TextInput
          ref={ref}
          style={[
            styles.input,
            styles.textArea,
            { minHeight: textAreaHeight },
            error && styles.inputError,
            style,
          ]}
          placeholderTextColor={theme.input.placeholder}
          multiline
          numberOfLines={numberOfLines}
          textAlignVertical="top"
          {...props}
        />
        {error && <Text style={styles.errorText}>{error}</Text>}
        {hint && !error && <Text style={styles.hintText}>{hint}</Text>}
      </View>
    );
  }
);

TextArea.displayName = 'TextArea';

const styles = StyleSheet.create({
  container: {
    marginBottom: theme.spacing.lg,
  },
  label: {
    ...theme.typography.textStyles.label,
    color: theme.text.primary,
    marginBottom: theme.spacing.sm,
  },
  required: {
    color: theme.accent.error,
  },
  input: {
    borderWidth: 1,
    borderColor: theme.input.border,
    borderRadius: theme.radius.input,
    paddingHorizontal: theme.spacing.inputPadding.horizontal,
    paddingVertical: theme.spacing.inputPadding.vertical,
    fontSize: theme.typography.fontSizes.lg,
    backgroundColor: theme.input.background,
    color: theme.input.text,
  },
  inputError: {
    borderColor: theme.accent.error,
  },
  textArea: {
    paddingTop: theme.spacing.inputPadding.vertical,
  },
  errorText: {
    ...theme.typography.textStyles.bodySmall,
    color: theme.accent.error,
    marginTop: theme.spacing.xs,
  },
  hintText: {
    ...theme.typography.textStyles.bodySmall,
    color: theme.text.tertiary,
    marginTop: theme.spacing.xs,
  },
});

// Export as default
export default Input;
