/**
 * Button Components
 * Reusable button components with consistent styling
 */

import React from 'react';
import {
  TouchableOpacity,
  Text,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacityProps,
  ViewStyle,
  TextStyle,
} from 'react-native';
import theme from '../theme';

export interface ButtonProps extends TouchableOpacityProps {
  title: string;
  onPress: () => void;
  loading?: boolean;
  disabled?: boolean;
  fullWidth?: boolean;
  variant?: 'primary' | 'secondary' | 'danger' | 'success';
  size?: 'small' | 'medium' | 'large';
}

/**
 * Get button styles based on variant
 */
const getButtonStyles = (
  variant: ButtonProps['variant'] = 'primary',
  disabled: boolean = false
): { container: ViewStyle; text: TextStyle } => {
  const baseContainer: ViewStyle = {
    borderRadius: theme.radius.button,
    alignItems: 'center',
    justifyContent: 'center',
    ...theme.shadows.button,
  };

  const baseText: TextStyle = {
    ...theme.typography.textStyles.button,
  };

  switch (variant) {
    case 'primary':
      return {
        container: {
          ...baseContainer,
          backgroundColor: disabled ? theme.button.primary.background : theme.button.primary.background,
          opacity: disabled ? theme.ui.DISABLED_OPACITY : 1,
        },
        text: {
          ...baseText,
          color: theme.button.primary.text,
        },
      };

    case 'secondary':
      return {
        container: {
          ...baseContainer,
          backgroundColor: disabled ? theme.button.secondary.background : theme.button.secondary.background,
          opacity: disabled ? theme.ui.DISABLED_OPACITY : 1,
        },
        text: {
          ...baseText,
          color: theme.button.secondary.text,
        },
      };

    case 'danger':
      return {
        container: {
          ...baseContainer,
          backgroundColor: disabled ? theme.button.danger.background : theme.button.danger.background,
          opacity: disabled ? theme.ui.DISABLED_OPACITY : 1,
        },
        text: {
          ...baseText,
          color: theme.button.danger.text,
        },
      };

    case 'success':
      return {
        container: {
          ...baseContainer,
          backgroundColor: disabled ? theme.button.success.background : theme.button.success.background,
          opacity: disabled ? theme.ui.DISABLED_OPACITY : 1,
        },
        text: {
          ...baseText,
          color: theme.button.success.text,
        },
      };

    default:
      return {
        container: baseContainer,
        text: baseText,
      };
  }
};

/**
 * Get padding based on size
 */
const getSizePadding = (size: ButtonProps['size'] = 'medium') => {
  switch (size) {
    case 'small':
      return {
        paddingHorizontal: theme.spacing.md,
        paddingVertical: theme.spacing.sm,
      };
    case 'large':
      return {
        paddingHorizontal: theme.spacing.xl,
        paddingVertical: theme.spacing.lg,
      };
    case 'medium':
    default:
      return {
        paddingHorizontal: theme.spacing.buttonPadding.horizontal,
        paddingVertical: theme.spacing.buttonPadding.vertical,
      };
  }
};

/**
 * Base Button Component
 */
export function Button({
  title,
  onPress,
  loading = false,
  disabled = false,
  fullWidth = false,
  variant = 'primary',
  size = 'medium',
  style,
  ...props
}: ButtonProps) {
  const isDisabled = disabled || loading;
  const variantStyles = getButtonStyles(variant, isDisabled);
  const sizeStyles = getSizePadding(size);

  return (
    <TouchableOpacity
      style={[
        styles.button,
        variantStyles.container,
        sizeStyles,
        fullWidth && styles.fullWidth,
        style,
      ]}
      onPress={onPress}
      disabled={isDisabled}
      activeOpacity={theme.ui.PRESSED_OPACITY}
      {...props}
    >
      {loading ? (
        <ActivityIndicator
          color={variantStyles.text.color}
          size="small"
        />
      ) : (
        <Text style={[styles.text, variantStyles.text]}>{title}</Text>
      )}
    </TouchableOpacity>
  );
}

/**
 * Primary Button (default variant)
 */
export function PrimaryButton(props: Omit<ButtonProps, 'variant'>) {
  return <Button {...props} variant="primary" />;
}

/**
 * Secondary Button
 */
export function SecondaryButton(props: Omit<ButtonProps, 'variant'>) {
  return <Button {...props} variant="secondary" />;
}

/**
 * Danger/Destructive Button
 */
export function DangerButton(props: Omit<ButtonProps, 'variant'>) {
  return <Button {...props} variant="danger" />;
}

/**
 * Success Button
 */
export function SuccessButton(props: Omit<ButtonProps, 'variant'>) {
  return <Button {...props} variant="success" />;
}

const styles = StyleSheet.create({
  button: {
    flexDirection: 'row',
  },
  fullWidth: {
    width: '100%',
  },
  text: {
    textAlign: 'center',
  },
});

// Export all button components
export default Button;
