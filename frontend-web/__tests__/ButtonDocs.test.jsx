/**
 * ButtonDocs.test.jsx
 * Button 문서 간단 렌더 테스트
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import ButtonDocs from '../app/component/docs/components/ButtonDocs.jsx';

describe('ButtonDocs', () => {
  it('renders section heading', () => {
    render(<ButtonDocs />);
    expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Button');
  });
});
