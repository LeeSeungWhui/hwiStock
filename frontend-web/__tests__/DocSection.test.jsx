/**
 * DocSection.test.jsx
 * 기본 렌더 테스트 (스냅샷 아님)
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import DocSection from '../app/component/docs/shared/DocSection.jsx';

describe('DocSection', () => {
  it('renders title and description', () => {
    render(
      <DocSection id="demo" title="데모 섹션" description={<p>설명 텍스트</p>}>
        <div>children</div>
      </DocSection>
    );
    expect(screen.getByRole('heading', { level: 2, name: '데모 섹션' })).toBeInTheDocument();
    expect(screen.getByText('설명 텍스트')).toBeInTheDocument();
    // section should reference the heading for a11y
    const section = screen.getByRole('region', { hidden: true }) || document.querySelector('section#demo');
    expect(section).toBeTruthy();
  });
});
