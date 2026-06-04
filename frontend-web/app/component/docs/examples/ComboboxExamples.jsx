/**
 * 파일명: ComboboxExamples.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Combobox 컴포넌트 예제 (EasyList/EasyObj 연동 포함)
 */
import { useState } from 'react';
import * as Lib from '@/app/lib';

/**
 * @description BasicComboDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const BasicComboDemo = () => {
  const [cityList] = useState(() => Lib.EasyList([{
    value: 'seoul',
    text: '서울'
  }, {
    value: 'busan',
    text: '부산'
  }, {
    value: 'incheon',
    text: '인천'
  }, {
    value: 'daegu',
    text: '대구'
  }]));
  const [profileDataObj] = useState(() => Lib.EasyObj({
    address: {
      city: 'incheon'
    }
  }));

  return <Lib.Combobox id="combobox-bound" dataList={cityList} dataObj={profileDataObj.address} dataKey="city" placeholder="도시 선택" status="success" statusMessage={`선택 도시: ${profileDataObj.address.city}`} />;
};

/**
 * @description BoundComboDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const BoundComboDemo = () => {
  const [cityList] = useState(() => Lib.EasyList([{
    value: 'seoul',
    text: '서울'
  }, {
    value: 'busan',
    text: '부산'
  }, {
    value: 'incheon',
    text: '인천'
  }, {
    value: 'daegu',
    text: '대구'
  }]));
  const [controlledCity, setControlledCity] = useState('seoul');

  return <div className="space-y-2">
      <Lib.Combobox id="combobox-controlled" dataList={cityList} value={controlledCity} onValueChange={setControlledCity} placeholder="도시 선택 (컨트롤드)" status="info" statusMessage={`value prop: ${controlledCity}`} />
      <div className="text-xs text-gray-500">
        초성검색 예: ㅅㅇ→서울, ㅂㅅ→부산
      </div>
    </div>;
};

/**
 * @description MultiComboDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const MultiComboDemo = () => {
  const [cityList] = useState(() => Lib.EasyList([{
    value: 'seoul',
    text: '서울'
  }, {
    value: 'busan',
    text: '부산'
  }, {
    value: 'incheon',
    text: '인천'
  }, {
    value: 'daegu',
    text: '대구'
  }]));
  const [profileDataObj] = useState(() => Lib.EasyObj({
    address: {
      favorites: ['seoul', 'busan']
    }
  }));

  return <Lib.Combobox id="combobox-multi" dataList={cityList} dataObj={profileDataObj.address} dataKey="favorites" multi multiSummary showSelectAll summaryText="{count}개 도시 선택" placeholder="좋아하는 도시 선택" status="warning" statusMessage="다중 선택 (EasyList selected/바운드 값 동시 반영)" />;
};

/**
 * @description LoadingComboDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const LoadingComboDemo = () => {
  const [cityList] = useState(() => Lib.EasyList([{
    value: '',
    text: '불러오는 중',
    placeholder: true
  }]));

  return <Lib.Combobox id="combobox-loading" dataList={cityList} status="loading" assistiveText="도시 목록을 불러오는 중입니다." disabled />;
};

/**
 * @description EmptyComboDemo 렌더링용 demo 컴포넌트. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const EmptyComboDemo = () => {
  const [cityList] = useState(() => Lib.EasyList([]));

  return <Lib.Combobox id="combobox-empty" dataList={cityList} status="empty" assistiveText="선택 가능한 도시가 없습니다." />;
};

export const basicExampleObj = {
  exampleId: 'basic',
  component: <BasicComboDemo />,
  description: 'EasyObj 바운드 모드 — dataObj/dataKey로 주소 객체와 동기화',
  code: `const cityList = Lib.EasyList([
  { value: 'seoul', text: '서울' },
  { value: 'busan', text: '부산' },
  { value: 'incheon', text: '인천' },
  { value: 'daegu', text: '대구' },
]);
const profileDataObj = Lib.EasyObj({ address: { city: 'incheon' } });

<Lib.Combobox
  dataList={cityList}
  dataObj={profileDataObj.address}
  dataKey="city"
  placeholder="도시 선택"
  status="success"
  statusMessage={\`선택 도시: \${profileDataObj.address.city}\`}
/>`
};

export const boundExampleObj = {
  exampleId: 'controlled',
  component: <BoundComboDemo />,
  description: '컨트롤드 모드 — value/onValueChange 조합',
  code: `const [controlledCity, setControlledCity] = useState('seoul');

<Lib.Combobox
  dataList={cityList}
  value={controlledCity}
  onValueChange={setControlledCity}
  placeholder="도시 선택 (컨트롤드)"
  status="info"
  statusMessage={\`value prop: \${controlledCity}\`}
/>`
};

export const multiExampleObj = {
  exampleId: 'multi',
  component: <MultiComboDemo />,
  description: 'multi + EasyObj 배열 바운드 — favorites 배열과 EasyList selected 동기화',
  code: `<Lib.Combobox
  dataList={cityList}
  dataObj={profileDataObj.address}
  dataKey="favorites"
  multi
  multiSummary
  showSelectAll
  summaryText="{count}개 도시 선택"
  placeholder="좋아하는 도시 선택"
  status="warning"
  statusMessage="다중 선택 (EasyList selected/바운드 값 동시 반영)"
/>`
};

export const summaryExampleObj = {
  exampleId: 'loading',
  component: <LoadingComboDemo />,
  description: '로딩/비활성화 — status="loading" + assistiveText',
  code: `<Lib.Combobox
  dataList={Lib.EasyList([{ value: '', text: '불러오는 중', placeholder: true }])}
  status="loading"
  assistiveText="도시 목록을 불러오는 중입니다."
  disabled
/>`
};

export const emptyExampleObj = {
  exampleId: 'empty',
  component: <EmptyComboDemo />,
  description: '빈 상태 — status="empty" 프리셋으로 항목 부재 안내와 assertive 라이브 영역',
  code: `<Lib.Combobox
  dataList={Lib.EasyList([])}
  status="empty"
  assistiveText="선택 가능한 도시가 없습니다."
/>`
};
