import { render, screen, fireEvent, act, waitFor } from '@testing-library/react'
import Select from '@/app/lib/component/Select'
import Combobox from '@/app/lib/component/Combobox'
import EasyObj from '@/app/lib/dataset/EasyObj'
import EasyList from '@/app/lib/dataset/EasyList'
import React, { useEffect, useState } from 'react'

const JobsFixture = [
  { id: '', label: '선택하세요', placeholder: true },
  { id: 'designer', label: '디자이너' },
  { id: 'developer', label: '개발자' },
  { id: 'pm', label: '프로덕트 매니저' },
]

describe('Select & Combobox binding contracts', () => {
  test('Select supports dataObj/dataKey and does not forward them to DOM', () => {
    const form = { profile: { job: 'developer' } }
    const jobs = JobsFixture
    render(
      <Select
        dataObj={form.profile}
        dataKey="job"
        dataList={jobs}
        valueKey="id"
        textKey="label"
      />,
    )

    const select = screen.getByRole('combobox')
    expect(select).toHaveValue('developer')
    expect(select).not.toHaveAttribute('dataobj')
    expect(select).not.toHaveAttribute('datakey')
  })

  test('Select synchronises with EasyList selected flags (single select)', async () => {
    let bound = null
    const Harness = ({ onReady }) => {
      const jobs = EasyList(
        JobsFixture.map((jobFixtureObj) => ({
          ...jobFixtureObj,
          selected: jobFixtureObj.id === 'developer',
        })),
      )
      useEffect(() => {
        onReady?.({ jobs })
      }, [jobs, onReady])
      return (
        <Select
          dataList={jobs}
          valueKey="id"
          textKey="label"
          status="success"
        />
      )
    }

    render(<Harness onReady={(exposed) => { bound = exposed }} />)
    await waitFor(() => expect(bound).not.toBeNull())

    const select = screen.getByRole('combobox')
    fireEvent.change(select, { target: { value: 'pm' } })
    await waitFor(() => expect(select).toHaveValue('pm'))

    const selectedIds = []
    bound.jobs.forAll((jobItemObj) => {
      if (jobItemObj.selected) selectedIds.push(jobItemObj.id)
    })
    expect(selectedIds).toEqual(['pm'])
  })

  test('Select reacts to external EasyObj bound value updates', async () => {
    let exposed = null
    const Harness = ({ onReady }) => {
      const filterStoreObj = EasyObj({ filters: { job: 'developer' } })
      const jobs = EasyList(JobsFixture)
      useEffect(() => {
        onReady?.({ filterStoreObj })
      }, [filterStoreObj, onReady])
      return (
        <Select
          dataObj={filterStoreObj.filters}
          dataKey="job"
          dataList={jobs}
          valueKey="id"
          textKey="label"
        />
      )
    }

    render(<Harness onReady={(value) => { exposed = value }} />)

    await waitFor(() => expect(exposed).not.toBeNull())

    const select = screen.getByRole('combobox')
    expect(select).toHaveValue('developer')

    await act(async () => {
      exposed.filterStoreObj.filters.job = 'pm'
    })

    await waitFor(() => {
      expect(select).toHaveValue('pm')
    })
  })

  test('Select controlled mode uses value/onValueChange contract', () => {
    const Controlled = () => {
      const [role, setRole] = useState('developer')
      const jobs = EasyList(JobsFixture)
      return (
        <>
          <Select
            dataList={jobs}
            valueKey="id"
            textKey="label"
            value={role}
            onValueChange={setRole}
            status="info"
          />
          <output data-testid="role-output">{role}</output>
        </>
      )
    }
    render(<Controlled />)

    const select = screen.getByRole('combobox')
    fireEvent.change(select, { target: { value: 'pm' } })

    expect(screen.getByTestId('role-output')).toHaveTextContent('pm')
  })

  test('Combobox multi-select synchronises with EasyObj array', async () => {
    let exposed = null
    const Harness = ({ onReady }) => {
      const filterStoreObj = EasyObj({ filters: { tags: ['seoul'] } })
      const cities = EasyList([
        { value: 'seoul', text: '서울' },
        { value: 'busan', text: '부산' },
        { value: 'incheon', text: '인천' },
      ])
      useEffect(() => {
        onReady?.({ filterStoreObj, cities })
      }, [filterStoreObj, cities, onReady])
      return (
        <Combobox
          dataList={cities}
          dataObj={filterStoreObj.filters}
          dataKey="tags"
          multi
          placeholder="도시 선택"
          status="warning"
        />
      )
    }

    render(<Harness onReady={(value) => { exposed = value }} />)

    await waitFor(() => expect(exposed).not.toBeNull())

    const button = screen.getByRole('button', { name: /서울/ })
    fireEvent.click(button)

    const busanOption = screen.getByRole('option', { name: '부산' })
    fireEvent.click(busanOption)
    expect(exposed.filterStoreObj.filters.tags).toEqual(
      expect.arrayContaining(['seoul', 'busan']),
    )

    await act(async () => {
      exposed.filterStoreObj.filters.set('tags', ['incheon'])
    })

    await waitFor(() =>
      expect(button).toHaveTextContent('인천'),
    )
  })

  test('Select empty status surface default message with assertive aria-live', () => {
    render(
      <Select
        dataList={[]}
        status="empty"
      />,
    )
    const message = screen.getByText('표시할 항목이 없습니다.')
    expect(message).toBeVisible()
    expect(message).toHaveAttribute('aria-live', 'assertive')
  })

  test('Combobox empty status surfaces default message with assertive aria-live', () => {
    render(
      <Combobox
        dataList={[]}
        status="empty"
      />,
    )
    const message = screen.getByText('표시할 항목이 없습니다.')
    expect(message).toBeVisible()
    expect(message).toHaveAttribute('aria-live', 'assertive')
  })
})
