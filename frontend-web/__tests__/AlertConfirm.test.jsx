import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import Alert from '../app/lib/component/Alert.jsx';
import Confirm from '../app/lib/component/Confirm.jsx';

describe('Alert accessibility', () => {
  it('exposes alertdialog semantics with aria-modal and label/description ids', () => {
    render(<Alert title="알림 제목" text="알림 본문" onClick={() => {}} />);

    const dialog = screen.getByRole('alertdialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');

    const labelledBy = dialog.getAttribute('aria-labelledby');
    const describedBy = dialog.getAttribute('aria-describedby');
    expect(labelledBy).toBeTruthy();
    expect(describedBy).toBeTruthy();
    expect(document.getElementById(labelledBy)).toHaveTextContent('알림 제목');
    expect(document.getElementById(describedBy)).toHaveTextContent('알림 본문');
  });
});

describe('Confirm accessibility', () => {
  it('exposes dialog semantics with aria-modal and label/description ids', () => {
    render(
      <Confirm
        title="확인 제목"
        text="확인 본문"
        onConfirm={() => {}}
        onCancel={() => {}}
      />
    );

    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');

    const labelledBy = dialog.getAttribute('aria-labelledby');
    const describedBy = dialog.getAttribute('aria-describedby');
    expect(labelledBy).toBeTruthy();
    expect(describedBy).toBeTruthy();
    expect(document.getElementById(labelledBy)).toHaveTextContent('확인 제목');
    expect(document.getElementById(describedBy)).toHaveTextContent('확인 본문');
  });
});
