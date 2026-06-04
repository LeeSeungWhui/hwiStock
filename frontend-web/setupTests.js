import '@testing-library/jest-dom'
import React from 'react'

// Vitest 환경에서 일부 레거시 컴포넌트가 `React` 전역을 기대하는 경우가 있어 보정한다.
globalThis.React = React
