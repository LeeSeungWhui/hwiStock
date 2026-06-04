/**
 * 파일명: IconDocs.jsx
 * 작성자: LSH
 * 갱신일: 2026-05-31
 * 설명: Icon 컴포넌트 문서
 */
import { iconExampleList } from '../examples/IconExamples';
import DocSection from '../shared/DocSection';
import CodeBlock from '../shared/CodeBlock';

/**
 * @description Icon 문서 섹션을 구성하고 예제/아이콘셋 링크를 렌더링. 입력/출력 계약을 함께 명시
 * @returns {JSX.Element}
 */
const IconDocs = () => {
  const iconSetLinks = [{
    prefix: 'ai:',
    name: 'Ant Design Icons',
    url: 'https://react-icons.github.io/react-icons/icons/ai/'
  }, {
    prefix: 'bi:',
    name: 'Box Icons',
    url: 'https://react-icons.github.io/react-icons/icons/bi/'
  }, {
    prefix: 'bs:',
    name: 'Bootstrap Icons',
    url: 'https://react-icons.github.io/react-icons/icons/bs/'
  }, {
    prefix: 'fi:',
    name: 'Feather Icons',
    url: 'https://react-icons.github.io/react-icons/icons/fi/'
  }, {
    prefix: 'hi:',
    name: 'Heroicons',
    url: 'https://react-icons.github.io/react-icons/icons/hi/'
  }, {
    prefix: 'io:',
    name: 'Ionicons',
    url: 'https://react-icons.github.io/react-icons/icons/io/'
  }, {
    prefix: 'md:',
    name: 'Material Design Icons',
    url: 'https://react-icons.github.io/react-icons/icons/md/'
  }, {
    prefix: 'ri:',
    name: 'Remix Icons',
    url: 'https://react-icons.github.io/react-icons/icons/ri/'
  }];
  return <DocSection id="icons" title="3. 아이콘 (Icon)" description={<div>
                    <p>Icon 컴포넌트는 다양한 아이콘 라이브러리를 통합하여 제공합니다.</p>
                    <p>각 아이콘 세트의 prefix를 사용하여 원하는 아이콘을 선택할 수 있습니다.</p>
                    <ul className="list-disc pl-5 mt-2 text-sm text-gray-600">
                        <li><code>icon</code>: 세트prefix:아이콘이름</li>
                        <li><code>size?</code>: 아이콘 크기 (기본: 1em)</li>
                        <li><code>color?</code>: 아이콘 색상</li>
                        <li><code>ariaLabel?</code>: 접근성 라벨</li>
                        <li><code>decorative?</code>: 장식용 여부(true면 숨김)</li>
                        <li><code>className?</code>: 추가 Tailwind 클래스</li>
                    </ul>
                    <div className="mt-4">
                        <h4 className="font-medium mb-2">사용 가능한 아이콘 세트</h4>
                        <ul className="list-disc list-inside text-sm space-y-2">
                            {iconSetLinks.map((set, index) => <li key={index} className="flex items-center gap-4">
                                    <span className="inline-block w-50">{set.name} ({set.prefix})</span>
                                    <a href={set.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-800 whitespace-nowrap">
                                        아이콘 보기 →
                                    </a>
                                </li>)}
                        </ul>
                    </div>
                </div>}>
            <div id="icon-basic" className="mb-8">
                <h3 className="text-lg font-medium mb-4">기본 사용법</h3>
                <div className="grid grid-cols-3 gap-8">
                    {iconExampleList.map(example => <div key={example.exampleId}>
                            {example.component}
                            <div className="mt-2 text-sm text-gray-600">
                                {example.description}
                            </div>
                            <CodeBlock code={example.code} />
                        </div>)}
                </div>
            </div>
        </DocSection>;
};

export default IconDocs;
