/**
 * React Testing Library tests for core UI.
 */

import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DropZone } from '../../src/components/dropzone/DropZone';

describe('DropZone', () => {
  it('renders with correct branding', () => {
    const mockCreateCase = jest.fn();
    render(<DropZone onCreateCase={mockCreateCase} />);

    expect(screen.getByText(/TWISTED/i)).toBeInTheDocument();
    expect(screen.getByText(/Liquid clarity for complex problems/i)).toBeInTheDocument();
  });

  it('enables submit only with valid input', async () => {
    const mockCreateCase = jest.fn();
    render(<DropZone onCreateCase={mockCreateCase} />);

    const input = screen.getByPlaceholderText(/e.g., 'Help Sarah with her insurance claim'/i);
    const button = screen.getByRole('button', { name: /Initialize Glass Engine/i });

    // Initially disabled
    expect(button).toBeDisabled();

    // Type valid query
    await userEvent.type(input, 'Help John with his employment dispute');
    expect(button).toBeEnabled();

    // Submit
    await userEvent.click(button);
    expect(mockCreateCase).toHaveBeenCalledWith(
      'Help John with his employment dispute',
      false  // deep research default
    );
  });

  it('toggles deep research option', async () => {
    const mockCreateCase = jest.fn();
    render(<DropZone onCreateCase={mockCreateCase} />);

    const checkbox = screen.getByLabelText(/Deep Research/i);
    await userEvent.click(checkbox);

    const input = screen.getByPlaceholderText(/e.g., 'Help Sarah/i);
    await userEvent.type(input, 'Test case');

    await userEvent.click(screen.getByRole('button', { name: /Initialize Glass Engine/i }));
    expect(mockCreateCase).toHaveBeenCalledWith('Test case', true);
  });
});
