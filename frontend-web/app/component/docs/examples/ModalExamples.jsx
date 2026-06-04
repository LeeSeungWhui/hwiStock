/**
 * 파일명: ModalExamples.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Modal 컴포넌트 예제
 */

import * as Lib from '@/app/lib';
import { useState } from 'react';

/**
 * @description BasicModalDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const BasicModalDemo = () => {
  const [isOpen, setIsOpen] = useState(false);

  return <div className="space-y-4">
      <Lib.Button onClick={() => setIsOpen(true)}>
        기본 모달 열기
      </Lib.Button>

      <Lib.Modal isOpen={isOpen} onClose={() => setIsOpen(false)}>
        <Lib.Modal.Header onClose={() => setIsOpen(false)}>
          <h2 className="text-xl font-semibold">기본 모달</h2>
        </Lib.Modal.Header>

        <Lib.Modal.Body>
          <p>기본적인 모달 예시입니다.</p>
        </Lib.Modal.Body>

        <Lib.Modal.Footer>
          <div className="flex justify-end">
            <Lib.Button onClick={() => setIsOpen(false)}>
              닫기
            </Lib.Button>
          </div>
        </Lib.Modal.Footer>
      </Lib.Modal>
    </div>;
};

/**
 * @description SizeModalDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const SizeModalDemo = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [currentSize, setCurrentSize] = useState('md');
  const modalSizeList = ['sm', 'md', 'lg', 'xl', 'full'];

  return <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {modalSizeList.map((size) => <Lib.Button key={size} onClick={() => {
          setCurrentSize(size);
          setIsOpen(true);
        }}>
          {size.toUpperCase()} 크기
        </Lib.Button>)}
      </div>

      <Lib.Modal isOpen={isOpen} onClose={() => setIsOpen(false)} size={currentSize}>
        <Lib.Modal.Header onClose={() => setIsOpen(false)}>
          <h2 className="text-xl font-semibold">{currentSize.toUpperCase()} 크기 모달</h2>
        </Lib.Modal.Header>

        <Lib.Modal.Body>
          <p>다양한 크기의 모달을 지원합니다.</p>
        </Lib.Modal.Body>
      </Lib.Modal>
    </div>;
};

/**
 * @description FormModalDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const FormModalDemo = () => {
  const [isOpen, setIsOpen] = useState(false);

  return <div className="space-y-4">
      <Lib.Button onClick={() => setIsOpen(true)}>
        폼 모달 열기
      </Lib.Button>

      <Lib.Modal isOpen={isOpen} onClose={() => setIsOpen(false)}>
        <Lib.Modal.Header onClose={() => setIsOpen(false)}>
          <h2 className="text-xl font-semibold">사용자 정보</h2>
        </Lib.Modal.Header>

        <Lib.Modal.Body>
          <form className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">이름</label>
              <Lib.Input className="mt-1" placeholder="이름을 입력하세요" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">이메일</label>
              <Lib.Input className="mt-1" type="email" placeholder="이메일을 입력하세요" />
            </div>
          </form>
        </Lib.Modal.Body>

        <Lib.Modal.Footer>
          <div className="flex justify-end gap-2">
            <Lib.Button onClick={() => setIsOpen(false)}>
              저장
            </Lib.Button>
            <Lib.Button variant="outline" onClick={() => setIsOpen(false)}>
              취소
            </Lib.Button>
          </div>
        </Lib.Modal.Footer>
      </Lib.Modal>
    </div>;
};

/**
 * @description DragModalDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const DragModalDemo = () => {
  const [isOpen, setIsOpen] = useState(false);

  return <div className="space-y-4">
      <Lib.Button onClick={() => setIsOpen(true)}>
        드래그 가능한 모달 열기
      </Lib.Button>

      <Lib.Modal isOpen={isOpen} onClose={() => setIsOpen(false)} draggable={true}>
        <Lib.Modal.Header onClose={() => setIsOpen(false)}>
          <h2 className="text-xl font-semibold">드래그 가능한 모달</h2>
          <p className="text-sm text-gray-500">헤더를 드래그해서 이동할 수 있습니다</p>
        </Lib.Modal.Header>

        <Lib.Modal.Body>
          <p>이 모달은 헤더 영역을 드래그하여 이동할 수 있습니다.</p>
          <p className="mt-2">화면 밖으로 나가지 않도록 제한되어 있습니다.</p>
        </Lib.Modal.Body>

        <Lib.Modal.Footer>
          <div className="flex justify-end">
            <Lib.Button onClick={() => setIsOpen(false)}>
              닫기
            </Lib.Button>
          </div>
        </Lib.Modal.Footer>
      </Lib.Modal>
    </div>;
};

/**
 * @description PositionModalDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const PositionModalDemo = () => {
  const [isOpen, setIsOpen] = useState(false);

  return <div className="space-y-4">
      <div className="flex gap-2">
        <Lib.Button onClick={() => setIsOpen(true)}>
          우측 상단에 모달 열기
        </Lib.Button>
      </div>

      <Lib.Modal isOpen={isOpen} onClose={() => setIsOpen(false)} top="20px" left="calc(100% - 20px - 512px)" draggable>
        <Lib.Modal.Header onClose={() => setIsOpen(false)}>
          <h2 className="text-xl font-semibold">위치 지정 모달</h2>
        </Lib.Modal.Header>

        <Lib.Modal.Body>
          <p>top, left prop으로 초기 위치를 지정할 수 있습니다.</p>
          <p className="mt-2">드래그하여 자유롭게 이동해보세요.</p>
        </Lib.Modal.Body>
      </Lib.Modal>
    </div>;
};

/**
 * @description Modal 예제 계약을 정의. 입력/출력 계약을 함께 명시
 * @returns { basicExampleList: Array, sizeExampleList: Array, formExampleList: Array, dragExampleList: Array, positionExampleList: Array }
 * @updated 2026-02-24
 */
export const basicExampleList = [{
  component: <BasicModalDemo />,
  description: "기본 모달",
  code: `const [isOpen, setIsOpen] = useState(false);

<Lib.Button onClick={() => setIsOpen(true)}>
    기본 모달 열기
</Lib.Button>

<Lib.Modal
    isOpen={isOpen}
    onClose={() => setIsOpen(false)}
>
    <Lib.Modal.Header onClose={() => setIsOpen(false)}>
        <h2 className="text-xl font-semibold">기본 모달</h2>
    </Lib.Modal.Header>

    <Lib.Modal.Body>
        <p>기본적인 모달 예시입니다.</p>
    </Lib.Modal.Body>

    <Lib.Modal.Footer>
        <div className="flex justify-end">
            <Lib.Button onClick={() => setIsOpen(false)}>
                닫기
            </Lib.Button>
        </div>
    </Lib.Modal.Footer>
</Lib.Modal>`
}];
export const sizeExampleList = [{
  component: <SizeModalDemo />,
  description: "모달 크기",
  code: `const [isOpen, setIsOpen] = useState(false);
const modalSizeList = ['sm', 'md', 'lg', 'xl', 'full'];
const [currentSize, setCurrentSize] = useState('md');

<div className="flex flex-wrap gap-2">
    {modalSizeList.map(size => (
        <Lib.Button
            key={size}
            onClick={() => {
                setCurrentSize(size);
                setIsOpen(true);
            }}
        >
            {size.toUpperCase()} 크기
        </Lib.Button>
    ))}
</div>

<Lib.Modal
    isOpen={isOpen}
    onClose={() => setIsOpen(false)}
    size={currentSize}
>
    <Lib.Modal.Header onClose={() => setIsOpen(false)}>
        <h2 className="text-xl font-semibold">{currentSize.toUpperCase()} 크기 모달</h2>
    </Lib.Modal.Header>

    <Lib.Modal.Body>
        <p>다양한 크기의 모달을 지원합니다.</p>
    </Lib.Modal.Body>
</Lib.Modal>`
}];
export const formExampleList = [{
  component: <FormModalDemo />,
  description: "폼이 포함된 모달",
  code: `const [isOpen, setIsOpen] = useState(false);

<Lib.Button onClick={() => setIsOpen(true)}>
    폼 모달 열기
</Lib.Button>

<Lib.Modal
    isOpen={isOpen}
    onClose={() => setIsOpen(false)}
>
    <Lib.Modal.Header onClose={() => setIsOpen(false)}>
        <h2 className="text-xl font-semibold">사용자 정보</h2>
    </Lib.Modal.Header>

    <Lib.Modal.Body>
        <form className="space-y-4">
            <div>
                <label className="block text-sm font-medium text-gray-700">이름</label>
                <Lib.Input className="mt-1" placeholder="이름을 입력하세요" />
            </div>
            <div>
                <label className="block text-sm font-medium text-gray-700">이메일</label>
                <Lib.Input className="mt-1" type="email" placeholder="이메일을 입력하세요" />
            </div>
        </form>
    </Lib.Modal.Body>

    <Lib.Modal.Footer>
        <div className="flex justify-end gap-2">
            <Lib.Button onClick={() => setIsOpen(false)}>
                저장
            </Lib.Button>
            <Lib.Button
                variant="outline"
                onClick={() => setIsOpen(false)}
            >
                취소
            </Lib.Button>
        </div>
    </Lib.Modal.Footer>
</Lib.Modal>`
}];
export const dragExampleList = [{
  component: <DragModalDemo />,
  description: "draggable prop을 true로 설정하면 모달을 드래그할 수 있습니다. 헤더 영역을 드래그하여 이동이 가능합니다.",
  code: `const [isOpen, setIsOpen] = useState(false);

<Lib.Modal
    isOpen={isOpen}
    onClose={() => setIsOpen(false)}
    draggable={true}
>
    <Lib.Modal.Header onClose={() => setIsOpen(false)}>
        <h2 className="text-xl font-semibold">드래그 가능한 모달</h2>
    </Lib.Modal.Header>

    <Lib.Modal.Body>
        <p>이 모달은 헤더 영역을 드래그하여 이동할 수 있습니다.</p>
    </Lib.Modal.Body>

    <Lib.Modal.Footer>
        <div className="flex justify-end">
            <Lib.Button onClick={() => setIsOpen(false)}>
                닫기
            </Lib.Button>
        </div>
    </Lib.Modal.Footer>
</Lib.Modal>`
}];
export const positionExampleList = [{
  component: <PositionModalDemo />,
  description: "top, left prop으로 모달의 초기 위치를 지정할 수 있습니다. 드래그 기능과 함께 사용하면 더욱 유용합니다.",
  code: `const [isOpen, setIsOpen] = useState(false);

<Lib.Modal
    isOpen={isOpen}
    onClose={() => setIsOpen(false)}
    top="20px"
    left="calc(100% - 20px - 512px)"
    draggable
>
    <Lib.Modal.Header onClose={() => setIsOpen(false)}>
        <h2 className="text-xl font-semibold">위치 지정 모달</h2>
    </Lib.Modal.Header>

    <Lib.Modal.Body>
        <p>top, left prop으로 초기 위치를 지정할 수 있습니다.</p>
    </Lib.Modal.Body>
</Lib.Modal>`
}];
