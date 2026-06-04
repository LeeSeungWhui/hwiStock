import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import Button from '../app/lib/component/Button.jsx';

describe('Button a11y/loading', () => {
  it('sets aria-busy when loading', () => {
    render(<Button loading>Loading</Button>);
    const btn = screen.getByRole('button', { name: /^Loading/ });
    expect(btn).toHaveAttribute('aria-busy', 'true');
    expect(btn).toBeDisabled();
    expect(screen.getByRole('status')).toHaveTextContent('처리중...');
  });
  it('sets aria-busy when status=loading', () => {
    render(<Button status="loading">Busy</Button>);
    const btn = screen.getByRole('button', { name: /Busy$/ });
    expect(btn).toHaveAttribute('aria-busy', 'true');
    expect(screen.getByRole('status')).toHaveTextContent('처리중...');
  });
});
