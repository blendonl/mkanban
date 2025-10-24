/**
 * Base Modal Component
 * Reusable modal with consistent styling and behavior
 */

import React, { ReactNode } from 'react';
import {
  Modal,
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  ModalProps,
} from 'react-native';
import theme from '../theme';

export interface BaseModalProps extends Partial<ModalProps> {
  visible: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  footer?: ReactNode;
  showCloseButton?: boolean;
  scrollable?: boolean;
  maxHeight?: number | string;
}

export default function BaseModal({
  visible,
  onClose,
  title,
  children,
  footer,
  showCloseButton = true,
  scrollable = true,
  maxHeight = '80%',
  animationType = 'slide',
  transparent = true,
  ...modalProps
}: BaseModalProps) {
  const ContentWrapper = scrollable ? ScrollView : View;

  return (
    <Modal
      visible={visible}
      animationType={animationType}
      transparent={transparent}
      onRequestClose={onClose}
      {...modalProps}
    >
      <View style={styles.overlay}>
        <View style={[styles.modal, { maxHeight }]}>
          {/* Header */}
          <View style={styles.header}>
            <Text style={styles.title}>{title}</Text>
            {showCloseButton && (
              <TouchableOpacity onPress={onClose} style={styles.closeButton}>
                <Text style={styles.closeButtonText}>✕</Text>
              </TouchableOpacity>
            )}
          </View>

          {/* Content */}
          <ContentWrapper
            style={scrollable ? styles.scrollContent : styles.content}
            contentContainerStyle={scrollable ? styles.scrollContentContainer : undefined}
            showsVerticalScrollIndicator={scrollable}
          >
            {children}
          </ContentWrapper>

          {/* Footer */}
          {footer && <View style={styles.footer}>{footer}</View>}
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: theme.modal.overlay,
    justifyContent: 'center',
    alignItems: 'center',
  },
  modal: {
    backgroundColor: theme.modal.background,
    borderRadius: theme.radius.modal,
    width: `${theme.ui.MODAL_WIDTH_PERCENTAGE * 100}%`,
    overflow: 'hidden',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: theme.spacing.modalPadding.vertical,
    borderBottomWidth: 1,
    borderBottomColor: theme.border.primary,
  },
  title: {
    ...theme.typography.textStyles.h3,
    color: theme.text.primary,
  },
  closeButton: {
    padding: theme.spacing.xs,
  },
  closeButtonText: {
    fontSize: theme.typography.fontSizes.xxxl,
    color: theme.text.secondary,
  },
  content: {
    padding: theme.spacing.modalPadding.vertical,
  },
  scrollContent: {
    maxHeight: theme.ui.PICKER_MAX_HEIGHT,
  },
  scrollContentContainer: {
    padding: theme.spacing.modalPadding.vertical,
  },
  footer: {
    padding: theme.spacing.modalPadding.vertical,
    borderTopWidth: 1,
    borderTopColor: theme.border.primary,
  },
});
