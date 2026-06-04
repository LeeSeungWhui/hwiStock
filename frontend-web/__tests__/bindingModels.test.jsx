import { describe, it, expect, vi } from 'vitest';
import React from 'react';
import '@testing-library/jest-dom';
import { renderHook, act, render, fireEvent } from '@testing-library/react';
import EasyObj from '../app/lib/dataset/EasyObj';
import EasyList from '../app/lib/dataset/EasyList';
import { getBoundValue, setBoundValue } from '../app/lib/binding';
import CheckButton from '../app/lib/component/CheckButton';

describe('EasyObj binding contract', () => {
    it('supports dotted key reads and writes via helper', () => {
        const { result } = renderHook(() => EasyObj({ user: { name: 'Ada' } }));

        act(() => {
            setBoundValue(result.current, 'user.name', 'Mina', { source: 'program' });
        });
        expect(getBoundValue(result.current, 'user.name')).toBe('Mina');

        act(() => {
            result.current.user = { name: 'Noa' };
        });
        expect(getBoundValue(result.current, 'user.name')).toBe('Noa');

        act(() => {
            result.current['user.name'] = 'Sia';
        });
        expect(getBoundValue(result.current, 'user.name')).toBe('Sia');
    });

    it('notifies subscribers with ctx metadata on direct assignment', () => {
        const { result } = renderHook(() => EasyObj({ profile: { name: 'Ada' } }));
        const listener = vi.fn();
        let unsubscribe;

        act(() => {
            unsubscribe = result.current.subscribe(listener);
        });

        act(() => {
            result.current.profile.name = 'Zia';
        });

        expect(listener).toHaveBeenCalledTimes(1);
        const changePayloadObj = listener.mock.calls[0][0];
        expect(changePayloadObj.ctx).toMatchObject({ dataKey: 'profile.name', modelType: 'obj', source: 'program' });
        expect(getBoundValue(result.current, 'profile.name')).toBe('Zia');

        act(() => {
            unsubscribe();
        });

        act(() => {
            result.current.profile.name = 'Ara';
        });

        expect(listener).toHaveBeenCalledTimes(1);
    });

    it('rebuilds root proxy on set and keeps subscriptions alive', () => {
        const { result } = renderHook(() => EasyObj({ profile: { name: 'Ada' } }));
        const listener = vi.fn();

        act(() => {
            result.current.subscribe(listener);
            result.current.set('', { contact: { email: 'ada@example.com' } }, { source: 'program' });
        });

        expect(getBoundValue(result.current, 'contact.email')).toBe('ada@example.com');
        expect(listener).toHaveBeenCalled();
        const changePayloadObj = listener.mock.calls[listener.mock.calls.length - 1][0];
        expect(changePayloadObj.ctx).toMatchObject({ dataKey: '', modelType: 'obj', source: 'program' });

        act(() => {
            result.current.copy({ contact: { email: 'ivy@example.com' } });
        });
        expect(getBoundValue(result.current, 'contact.email')).toBe('ivy@example.com');
    });

    it('keeps cached child proxies in sync after root reset', () => {
        const { result } = renderHook(() => EasyObj({ profile: { name: 'Ada' } }));
        const branch = result.current.profile;
        expect(branch.name).toBe('Ada');

        act(() => {
            result.current.set('', { profile: { name: 'Mia' } }, { source: 'program' });
        });

        expect(branch.name).toBe('Mia');
        expect(branch.get('name')).toBe('Mia');
    });

    it('refreshes cached child proxies when replaced with primitive', () => {
        const { result } = renderHook(() => EasyObj({ profile: { name: 'Ada' } }));
        const branch = result.current.profile;
        expect(branch.name).toBe('Ada');

        act(() => {
            result.current.profile = 'Solo';
        });

        expect(branch.name).toBeUndefined();
        expect(branch.valueOf()).toBe('Solo');
    });

    it('keeps native File/Blob values readable without proxy brand errors', () => {
        const nativeValue = typeof File !== 'undefined'
            ? new File(['hello'], 'hello.txt', { type: 'text/plain' })
            : new Blob(['hello'], { type: 'text/plain' });

        const { result } = renderHook(() => EasyObj({ attachment: nativeValue }));

        expect(result.current.attachment).toBe(nativeValue);
        expect(() => result.current.attachment.size).not.toThrow();
        expect(result.current.attachment.size).toBe(nativeValue.size);
        if ('name' in nativeValue) {
            expect(result.current.attachment.name).toBe(nativeValue.name);
        }
    });
});

describe('EasyList binding contract', () => {
    it('tracks nested mutations and dotted keys', () => {
        const { result } = renderHook(() => EasyList([{ id: 1, name: 'Ada' }, { id: 2, name: 'Mia' }]));

        act(() => {
            setBoundValue(result.current, '1.name', 'Nia', { source: 'program' });
        });
        expect(getBoundValue(result.current, '1.name')).toBe('Nia');

        act(() => {
            result.current.push({ id: 3, name: 'Ona' });
        });
        expect(getBoundValue(result.current, '2.name')).toBe('Ona');

        act(() => {
            result.current.splice(1, 1, { id: 4, name: 'Pia' });
        });
        expect(getBoundValue(result.current, '1.name')).toBe('Pia');
    });

    it('emits ctx for list subscriptions', () => {
        const { result } = renderHook(() => EasyList([{ id: 1, name: 'Ada' }]));
        const listener = vi.fn();

        act(() => {
            result.current.subscribe(listener);
        });

        act(() => {
            result.current[0].name = 'Gia';
        });

        expect(listener).toHaveBeenCalled();
        const changePayloadObj = listener.mock.calls[0][0];
        expect(changePayloadObj.ctx).toMatchObject({ dataKey: '0.name', modelType: 'list', source: 'program' });
        expect(getBoundValue(result.current, '0.name')).toBe('Gia');
    });

    it('recreates root proxy when replacing entire list', () => {
        const { result } = renderHook(() => EasyList([{ id: 1, name: 'Ada' }]));
        const listener = vi.fn();

        act(() => {
            result.current.subscribe(listener);
            result.current.set('', [{ id: 9, name: 'Nia' }], { source: 'program' });
        });

        expect(listener).toHaveBeenCalled();
        expect(getBoundValue(result.current, '0.name')).toBe('Nia');
        const changePayloadObj = listener.mock.calls[listener.mock.calls.length - 1][0];
        expect(changePayloadObj.ctx).toMatchObject({ dataKey: '', modelType: 'list' });
    });

    it('keeps cached item proxies in sync after root reset', () => {
        const { result } = renderHook(() => EasyList([{ id: 1, name: 'Ada' }]));
        const firstItem = result.current[0];
        expect(firstItem.name).toBe('Ada');

        act(() => {
            result.current.set('', [{ id: 1, name: 'Nia' }], { source: 'program' });
        });

        expect(firstItem.name).toBe('Nia');
        expect(firstItem.get('name')).toBe('Nia');
    });

    it('refreshes cached list items when replaced with primitive', () => {
        const { result } = renderHook(() => EasyList([{ id: 1, name: 'Ada' }]));
        const firstItem = result.current[0];
        expect(firstItem.name).toBe('Ada');

        act(() => {
            result.current[0] = 'Solo';
        });

        expect(firstItem.name).toBeUndefined();
        expect(firstItem.valueOf()).toBe('Solo');
    });
});

describe('Component event pipeline', () => {
    it('preserves native event prototype for toggle buttons', () => {
        const handleChange = vi.fn((evt) => {
            expect(typeof evt.preventDefault).toBe('function');
            evt.preventDefault();
            const detail = evt.detail && typeof evt.detail === 'object'
                ? evt.detail
                : { value: evt.target?.value, ctx: undefined };
            const normalized = detail.value === 'true' ? true : detail.value;
            expect(normalized).toBe(true);
        });

        const { getByRole } = render(<CheckButtonHarness onChange={handleChange} />);
        const button = getByRole('button', { name: /toggle/i });
        expect(button).toHaveAttribute('aria-pressed', 'false');

        fireEvent.click(button);

        expect(handleChange).toHaveBeenCalledTimes(1);
        expect(button).toHaveAttribute('aria-pressed', 'true');
    });
});

const CheckButtonHarness = ({ onChange }) => {
    const model = EasyObj({ toggle: false });
    return (
        <CheckButton dataObj={model} dataKey="toggle" onChange={onChange}>
            Toggle
        </CheckButton>
    );
};
