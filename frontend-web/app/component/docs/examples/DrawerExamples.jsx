/**
 * 파일명: DrawerExamples.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Drawer 컴포넌트 예제
 */
import * as Lib from '@/app/lib';
import { useState } from 'react';

/**
 * @description DrawerDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const DrawerDemo = ({ buttonLabel, children, ...drawerProps }) => {
  const [isOpen, setIsOpen] = useState(false);

  return <div>
      <Lib.Button onClick={() => setIsOpen(true)}>{buttonLabel}</Lib.Button>
      <Lib.Drawer isOpen={isOpen} onClose={() => setIsOpen(false)} {...drawerProps}>
        {children}
      </Lib.Drawer>
    </div>;
};

export const basicExampleObj = {
  exampleId: 'basic',
  component: <DrawerDemo buttonLabel="오른쪽 드로어 (기본)" side="right" resizable collapseButton>
      <div className="p-3">내용 없음</div>
    </DrawerDemo>,
  description: '오른쪽에서 열리는 기본 드로어 (리사이즈 가능, 핸들 포함)',
  code: '<Lib.Drawer isOpen={open} onClose={close} side="right" resizable collapseButton>내용 없음</Lib.Drawer>'
};

export const rightSizeExampleObj = {
  exampleId: 'rightSized',
  component: <DrawerDemo buttonLabel='오른쪽 드로어 (size="min-[1468px]:w-[360px]")' side="right" size="min-[1468px]:w-[360px]" collapseButton>
      <div className="p-3">width 360px</div>
    </DrawerDemo>,
  description: '오른쪽 드로어 너비를 Tailwind px 클래스 문자열로 지정(size="min-[1468px]:w-[360px]")',
  code: '<Lib.Drawer isOpen={open} onClose={close} side="right" size="min-[1468px]:w-[360px]" collapseButton>width 360px</Lib.Drawer>'
};

export const leftSizeExampleObj = {
  exampleId: 'leftSized',
  component: <DrawerDemo buttonLabel='왼쪽 드로어 (size="min-[1468px]:w-[420px]")' side="left" size="min-[1468px]:w-[420px]" collapseButton>
      <div className="p-3">width 420px</div>
    </DrawerDemo>,
  description: '왼쪽 드로어 너비를 Tailwind px 클래스 문자열로 지정(size="min-[1468px]:w-[420px]")',
  code: '<Lib.Drawer isOpen={open} onClose={close} side="left" size="min-[1468px]:w-[420px]" collapseButton>width 420px</Lib.Drawer>'
};

export const topExampleObj = {
  exampleId: 'top',
  component: <DrawerDemo buttonLabel='위쪽 드로어 (size="min-[1468px]:h-[220px]")' side="top" size="min-[1468px]:h-[220px]" collapseButton>
      <div className="p-3">height 220px</div>
    </DrawerDemo>,
  description: '위쪽 드로어 높이를 Tailwind px 클래스 문자열로 지정(size="min-[1468px]:h-[220px]")',
  code: '<Lib.Drawer isOpen={open} onClose={close} side="top" size="min-[1468px]:h-[220px]" collapseButton>height 220px</Lib.Drawer>'
};

export const bottomExampleObj = {
  exampleId: 'bottom',
  component: <DrawerDemo buttonLabel='아래쪽 드로어 (size="min-[1468px]:h-[260px]")' side="bottom" size="min-[1468px]:h-[260px]" collapseButton>
      <div className="p-3">height 260px</div>
    </DrawerDemo>,
  description: '아래쪽 드로어 높이를 Tailwind px 클래스 문자열로 지정(size="min-[1468px]:h-[260px]")',
  code: '<Lib.Drawer isOpen={open} onClose={close} side="bottom" size="min-[1468px]:h-[260px]" collapseButton>height 260px</Lib.Drawer>'
};

export const cardExampleObj = {
  exampleId: 'card',
  component: <DrawerDemo buttonLabel="카드 드로어" side="right" collapseButton>
      <Lib.Card title="카드 샘플">
        <p>드로어 안 카드</p>
      </Lib.Card>
    </DrawerDemo>,
  description: '카드 컴포넌트를 포함한 드로어',
  code: '<Lib.Drawer isOpen={open} onClose={close} side="right" collapseButton><Lib.Card title="카드 샘플">드로어 안 카드</Lib.Card></Lib.Drawer>'
};

export const menuExampleObj = {
  exampleId: 'menu',
  component: <DrawerDemo buttonLabel="메뉴 드로어" side="left" collapseButton>
      <ul className="p-4 space-y-2">
        <li><button type="button" className="block text-left">메뉴 1</button></li>
        <li><button type="button" className="block text-left">메뉴 2</button></li>
        <li><button type="button" className="block text-left">메뉴 3</button></li>
      </ul>
    </DrawerDemo>,
  description: '리스트 메뉴를 담은 드로어',
  code: '<Lib.Drawer isOpen={open} onClose={close} side="left" collapseButton><ul className="p-4 space-y-2"><li>...</li></ul></Lib.Drawer>'
};
