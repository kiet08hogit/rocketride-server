import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { PlanPicker } from './PlanPicker';
import type { CheckoutPlan } from './types';

describe('PlanPicker', () => {
	it('renders an action plan as a native <a> tag with target="_blank" and rel="noopener noreferrer"', () => {
		const mockActionPlan: CheckoutPlan = {
			id: 'price_free',
			stripePriceId: 'price_free',
			nickname: 'Free',
			amountCents: 0,
			interval: 'month',
			metadata: {
				action: {
					type: 'link',
					label: 'Get started',
					url: 'https://rocketride.org/docs',
				},
			},
		};

		render(<PlanPicker plans={[mockActionPlan]} />);

		const link = screen.getByRole('link', { name: 'Get started' });
		expect(link).toBeInTheDocument();
		// Asserting native navigation works via the href
		expect(link).toHaveAttribute('href', 'https://rocketride.org/docs');
		// Asserting security regression fix
		expect(link).toHaveAttribute('target', '_blank');
		expect(link).toHaveAttribute('rel', 'noopener noreferrer');
	});

	it('prevents default native navigation when onActionClick is provided', async () => {
		const mockActionPlan: CheckoutPlan = {
			id: 'price_enterprise',
			stripePriceId: 'price_enterprise',
			nickname: 'Enterprise',
			amountCents: 0,
			interval: 'month',
			metadata: {
				action: {
					type: 'link',
					label: 'Contact us',
					url: 'https://rocketride.org/contact',
				},
			},
		};

		const onActionClick = vi.fn();
		render(<PlanPicker plans={[mockActionPlan]} onActionClick={onActionClick} />);

		const link = screen.getByRole('link', { name: 'Contact us' });
		
		const event = new MouseEvent('click', { bubbles: true, cancelable: true });
		const defaultPrevented = !link.dispatchEvent(event);
		
		// The custom handler should be called instead of native navigation
		expect(defaultPrevented).toBe(true);
		expect(onActionClick).toHaveBeenCalledWith(mockActionPlan, mockActionPlan.metadata.action);
	});

	it('renders a mailto action with no target or rel, and handles default navigation if no onActionClick', () => {
		const mockMailtoPlan: CheckoutPlan = {
			id: 'price_contact',
			stripePriceId: 'price_contact',
			nickname: 'Contact',
			amountCents: 0,
			interval: 'month',
			metadata: {
				action: {
					type: 'mailto',
					label: 'Email us',
					url: 'hello@rocketride.org',
					subject: 'Enterprise Plan',
				},
			},
		};

		render(<PlanPicker plans={[mockMailtoPlan]} />);

		const link = screen.getByRole('link', { name: 'Email us' });
		expect(link).toHaveAttribute('href', 'mailto:hello@rocketride.org?subject=Enterprise%20Plan');
		expect(link).not.toHaveAttribute('target');
		expect(link).not.toHaveAttribute('rel');

		const event = new MouseEvent('click', { bubbles: true, cancelable: true });
		const defaultPrevented = !link.dispatchEvent(event);
		
		// Native navigation should happen (default not prevented)
		expect(defaultPrevented).toBe(false);
	});
});
