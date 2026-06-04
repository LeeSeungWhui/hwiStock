/**
 * 파일명: DataClassExamples.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: DataClass 컴포넌트 예제
 */
import { useState } from 'react';
import * as Lib from '@/app/lib';

/**
 * @description EasyObj 예제 컴포넌트를 렌더링. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 * @updated 2026-02-27
 */
const EasyObjExample = () => {
  const [dataObj] = useState(() => Lib.EasyObj({
    name: '홍길동',
    age: 20,
    hobbies: ['독서', '운동'],
    address: {
      city: '서울',
      street: '강남대로'
    }
  }));
  return <div className="space-y-4">
            <div className="flex gap-2">
                <Lib.Button onClick={() => {
        dataObj.age += 1;
      }}>
                    나이 증가
                </Lib.Button>
                <Lib.Button onClick={() => {
        dataObj.hobbies.push('여행');
      }}>
                    취미 추가
                </Lib.Button>
                <Lib.Button onClick={() => {
        dataObj.address.city = '부산';
      }}>
                    도시 변경
                </Lib.Button>
            </div>
            <pre className="bg-gray-100 p-4 rounded-lg overflow-auto">
                {JSON.stringify(dataObj, null, 2)}
            </pre>
        </div>;
};

/**
 * @description EasyList 예제 컴포넌트를 렌더링. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 * @updated 2026-02-27
 */
const EasyListExample = () => {
  const [taskList] = useState(() => Lib.EasyList([{
    id: 1,
    text: '할 일 1'
  }, {
    id: 2,
    text: '할 일 2'
  }]));
  return <div className="space-y-4">
            <div className="flex gap-2">
                <Lib.Button onClick={() => taskList.push({
        id: taskList.length + 1,
        text: `할 일 ${taskList.length + 1}`
      })}>
                    항목 추가
                </Lib.Button>
                <Lib.Button onClick={() => taskList.pop()}>
                    마지막 항목 제거
                </Lib.Button>
                <Lib.Button onClick={() => taskList.forAll(taskItemObj => {
        taskItemObj.text += ' (완료)';
      })}>
                    모든 항목 완료
                </Lib.Button>
            </div>
            <pre className="bg-gray-100 p-4 rounded-lg overflow-auto">
                {JSON.stringify(taskList, null, 2)}
            </pre>
        </div>;
};

/**
 * @description DataClass 예제 계약을 정의. 입력/출력 계약을 함께 명시
 * @updated 2026-02-24
 * 처리 규칙: 입력값과 상태를 검증해 UI/데이터 흐름을 안전하게 유지한다.
 */
export const easyObjExampleList = [{
  component: <EasyObjExample />,
  description: "EasyObj는 객체의 중첩된 속성까지 자동으로 상태를 관리합니다.",
  code: `const dataObj = Lib.EasyObj({
    name: '홍길동',
    age: 20,
    hobbies: ['독서', '운동'],
    address: {
        city: '서울',
        street: '강남대로'
    }
});

// 상태 변경 시 자동으로 리렌더링
dataObj.age += 1;
dataObj.hobbies.push('여행');
dataObj.address.city = '부산';`
}];
export const easyListExampleList = [{
  component: <EasyListExample />,
  description: "EasyList는 배열 메서드를 지원하며 각 항목의 상태도 자동으로 관리합니다.",
  code: `const taskList = Lib.EasyList([
    { id: 1, text: '할 일 1' },
    { id: 2, text: '할 일 2' }
]);

// 배열 메서드 사용
taskList.push({ id: 3, text: '할 일 3' });
taskList.pop();

// forAll 메서드로 모든 항목 수정
taskList.forAll(item => {
    item.text += ' (완료)';
});`
}];
