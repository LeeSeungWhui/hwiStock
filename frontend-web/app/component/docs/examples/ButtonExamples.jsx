/**
 * 파일명: ButtonExamples.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Button 컴포넌트 예제
 */
import * as Lib from '@/app/lib';

/**
 * @description Button 예제 계약을 정의. 입력/출력 계약을 함께 명시
 * @updated 2026-02-24
 * 처리 규칙: 입력값과 상태를 검증해 UI/데이터 흐름을 안전하게 유지한다.
 */
export const variantExampleList = [{
  exampleId: 'primary',
  component: <Lib.Button>기본 버튼</Lib.Button>,
  description: "기본 버튼 (Primary)",
  code: "<Lib.Button>기본 버튼</Lib.Button>"
}, {
  exampleId: 'secondary',
  component: <Lib.Button variant="secondary">Secondary</Lib.Button>,
  description: "Secondary 버튼",
  code: '<Lib.Button variant="secondary">Secondary</Lib.Button>'
}, {
  exampleId: 'outline',
  component: <Lib.Button variant="outline">Outline</Lib.Button>,
  description: "Outline 버튼",
  code: '<Lib.Button variant="outline">Outline</Lib.Button>'
}, {
  exampleId: 'ghost',
  component: <Lib.Button variant="ghost">Ghost</Lib.Button>,
  description: "Ghost 버튼",
  code: '<Lib.Button variant="ghost">Ghost</Lib.Button>'
}, {
  exampleId: 'danger',
  component: <Lib.Button variant="danger">Danger</Lib.Button>,
  description: "Danger 버튼",
  code: '<Lib.Button variant="danger">Danger</Lib.Button>'
}, {
  exampleId: 'success',
  component: <Lib.Button variant="success">Success</Lib.Button>,
  description: "Success 버튼",
  code: '<Lib.Button variant="success">Success</Lib.Button>'
}, {
  exampleId: 'warning',
  component: <Lib.Button variant="warning">Warning</Lib.Button>,
  description: "Warning 버튼",
  code: '<Lib.Button variant="warning">Warning</Lib.Button>'
}, {
  exampleId: 'link',
  component: <Lib.Button variant="link">Link Button</Lib.Button>,
  description: "Link 스타일 버튼",
  code: '<Lib.Button variant="link">Link Button</Lib.Button>'
}, {
  exampleId: 'dark',
  component: <Lib.Button variant="dark">Dark</Lib.Button>,
  description: "Dark 버튼",
  code: '<Lib.Button variant="dark">Dark</Lib.Button>'
}, {
  exampleId: 'gradient',
  component: <Lib.Button className="bg-gradient-to-r from-purple-500 to-pink-500
                hover:from-purple-600 hover:to-pink-600">
                그라데이션
            </Lib.Button>,
  description: "커스텀 버튼",
  code: `<Lib.Button
    className="bg-gradient-to-r from-purple-500 to-pink-500
    hover:from-purple-600 hover:to-pink-600"
>
    그라데이션
</Lib.Button>`
}, {
  exampleId: 'icon',
  component: <Lib.Button>
                <Lib.Icon icon="ri:RiSearchLine" className="w-5 h-5 mr-2" />
                검색
            </Lib.Button>,
  description: "아이콘이 있는 버튼",
  code: `<Lib.Button>
    <Lib.Icon icon="ri:RiSearchLine" className="w-5 h-5 mr-2" />
    검색
</Lib.Button>`
}, {
  exampleId: 'disabled',
  component: <Lib.Button disabled>Disabled</Lib.Button>,
  description: "비활성화 버튼",
  code: '<Lib.Button disabled>Disabled</Lib.Button>'
}];
export const sizeExampleList = [{
  exampleId: 'small',
  component: <Lib.Button size="sm">Small</Lib.Button>,
  description: "Small 버튼",
  code: '<Lib.Button size="sm">Small</Lib.Button>'
}, {
  exampleId: 'medium',
  component: <Lib.Button size="md">Medium</Lib.Button>,
  description: "Medium 버튼",
  code: '<Lib.Button size="md">Medium</Lib.Button>'
}, {
  exampleId: 'large',
  component: <Lib.Button size="lg">Large</Lib.Button>,
  description: "Large 버튼",
  code: '<Lib.Button size="lg">Large</Lib.Button>'
}];
