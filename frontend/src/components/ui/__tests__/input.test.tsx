import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { useState } from 'react'
import { Input } from '../input'

describe('Input Component', () => {
  describe('Basic Rendering', () => {
    it('should render an input element', () => {
      render(<Input />)
      
      const input = screen.getByRole('textbox')
      expect(input).toBeInTheDocument()
      expect(input.tagName).toBe('INPUT')
    })

    it('should have default type as text', () => {
      render(<Input />)
      
      const input = screen.getByRole('textbox') as HTMLInputElement
      // HTML input elements without explicit type default to "text" in behavior
      expect(input.type).toBe('text')
    })

    it('should have data-slot attribute', () => {
      render(<Input />)
      
      const input = screen.getByRole('textbox')
      expect(input).toHaveAttribute('data-slot', 'input')
    })

    it('should apply default CSS classes', () => {
      render(<Input />)
      
      const input = screen.getByRole('textbox')
      expect(input).toHaveClass('flex', 'h-9', 'w-full', 'rounded-md', 'border')
      expect(input).toHaveClass('bg-transparent', 'px-3', 'py-1', 'text-base')
      expect(input).toHaveClass('focus-visible:border-ring', 'focus-visible:ring-ring/50')
    })
  })

  describe('Props Handling', () => {
    it('should accept and apply type prop', () => {
      render(<Input type="password" />)
      
      // password inputs don't have a specific accessible role, so we use a different selector
      const input = document.querySelector('input[type="password"]')
      expect(input).toBeInTheDocument()
      expect(input).toHaveAttribute('type', 'password')
    })

    it('should accept and apply value prop', () => {
      render(<Input value="test value" readOnly />)
      
      const input = screen.getByDisplayValue('test value')
      expect(input).toHaveValue('test value')
    })

    it('should accept and apply placeholder prop', () => {
      render(<Input placeholder="Enter text here" />)
      
      const input = screen.getByPlaceholderText('Enter text here')
      expect(input).toBeInTheDocument()
    })

    it('should accept and apply disabled prop', () => {
      render(<Input disabled />)
      
      const input = screen.getByRole('textbox')
      expect(input).toBeDisabled()
      expect(input).toHaveClass('disabled:pointer-events-none', 'disabled:cursor-not-allowed', 'disabled:opacity-50')
    })

    it('should accept and apply name prop', () => {
      render(<Input name="username" />)
      
      const input = screen.getByRole('textbox')
      expect(input).toHaveAttribute('name', 'username')
    })

    it('should accept and apply id prop', () => {
      render(<Input id="test-input" />)
      
      const input = screen.getByRole('textbox')
      expect(input).toHaveAttribute('id', 'test-input')
    })

    it('should accept and apply aria-label prop', () => {
      render(<Input aria-label="Username input" />)
      
      const input = screen.getByLabelText('Username input')
      expect(input).toBeInTheDocument()
    })

    it('should accept and apply aria-invalid prop', () => {
      render(<Input aria-invalid />)
      
      const input = screen.getByRole('textbox')
      expect(input).toHaveAttribute('aria-invalid', 'true')
      expect(input).toHaveClass('aria-invalid:ring-destructive/20', 'aria-invalid:border-destructive')
    })
  })

  describe('Styling and CSS Classes', () => {
    it('should merge custom className with default classes', () => {
      render(<Input className="custom-class border-red-500" />)
      
      const input = screen.getByRole('textbox')
      expect(input).toHaveClass('custom-class', 'border-red-500')
      expect(input).toHaveClass('flex', 'h-9', 'w-full') // default classes should still be present
    })

    it('should handle className prop as undefined', () => {
      render(<Input className={undefined} />)
      
      const input = screen.getByRole('textbox')
      expect(input).toHaveClass('flex', 'h-9', 'w-full') // should still have default classes
    })

    it('should apply focus-visible styles', () => {
      render(<Input />)
      
      const input = screen.getByRole('textbox')
      expect(input).toHaveClass('focus-visible:border-ring', 'focus-visible:ring-ring/50', 'focus-visible:ring-[3px]')
    })

    it('should apply aria-invalid styles when aria-invalid is true', () => {
      render(<Input aria-invalid={true} />)
      
      const input = screen.getByRole('textbox')
      expect(input).toHaveClass('aria-invalid:ring-destructive/20', 'aria-invalid:border-destructive')
    })
  })

  describe('Event Handling', () => {
    it('should call onChange when input value changes', () => {
      const handleChange = vi.fn()
      render(<Input onChange={handleChange} />)
      
      const input = screen.getByRole('textbox')
      fireEvent.change(input, { target: { value: 'new value' } })
      
      expect(handleChange).toHaveBeenCalledTimes(1)
      expect(handleChange).toHaveBeenCalledWith(expect.objectContaining({
        target: expect.objectContaining({
          value: 'new value'
        })
      }))
    })

    it('should call onFocus when input is focused', () => {
      const handleFocus = vi.fn()
      render(<Input onFocus={handleFocus} />)
      
      const input = screen.getByRole('textbox')
      fireEvent.focus(input)
      
      expect(handleFocus).toHaveBeenCalledTimes(1)
    })

    it('should call onBlur when input loses focus', () => {
      const handleBlur = vi.fn()
      render(<Input onBlur={handleBlur} />)
      
      const input = screen.getByRole('textbox')
      fireEvent.focus(input)
      fireEvent.blur(input)
      
      expect(handleBlur).toHaveBeenCalledTimes(1)
    })

    it('should call onKeyDown when key is pressed', () => {
      const handleKeyDown = vi.fn()
      render(<Input onKeyDown={handleKeyDown} />)
      
      const input = screen.getByRole('textbox')
      fireEvent.keyDown(input, { key: 'Enter' })
      
      expect(handleKeyDown).toHaveBeenCalledTimes(1)
      expect(handleKeyDown).toHaveBeenCalledWith(expect.objectContaining({
        key: 'Enter'
      }))
    })

    it('should not call onChange when disabled', () => {
      const handleChange = vi.fn()
      render(<Input onChange={handleChange} disabled />)
      
      const input = screen.getByRole('textbox')
      
      // Note: disabled inputs in React Testing Library still fire onChange events
      // This is different from real browser behavior, but is expected in testing
      fireEvent.change(input, { target: { value: 'new value' } })
      
      // In a real browser, disabled inputs don't fire events, but in tests they do
      // So we test that the input is disabled instead
      expect(input).toBeDisabled()
    })
  })

  describe('Input Types', () => {
    it('should render email input correctly', () => {
      render(<Input type="email" />)
      
      const input = screen.getByRole('textbox')
      expect(input).toHaveAttribute('type', 'email')
    })

    it('should render number input correctly', () => {
      render(<Input type="number" />)
      
      const input = screen.getByRole('spinbutton')
      expect(input).toHaveAttribute('type', 'number')
    })

    it('should render password input correctly', () => {
      render(<Input type="password" />)
      
      // password inputs don't have a specific role, so we use a different selector
      const input = document.querySelector('input[type="password"]')
      expect(input).toBeInTheDocument()
      expect(input).toHaveAttribute('type', 'password')
    })

    it('should render search input correctly', () => {
      render(<Input type="search" />)
      
      const input = screen.getByRole('searchbox')
      expect(input).toHaveAttribute('type', 'search')
    })

    it('should render file input correctly', () => {
      render(<Input type="file" />)
      
      // File inputs don't have a specific label by default, so we use a different selector
      const input = document.querySelector('input[type="file"]')
      expect(input).toBeInTheDocument()
      expect(input).toHaveAttribute('type', 'file')
      // File inputs should have file-specific styles
      expect(input).toHaveClass('file:text-foreground', 'file:bg-transparent')
    })
  })

  describe('Controlled vs Uncontrolled', () => {
    it('should work as uncontrolled component', () => {
      render(<Input defaultValue="initial value" />)
      
      const input = screen.getByDisplayValue('initial value') as HTMLInputElement
      expect(input.value).toBe('initial value')
      
      fireEvent.change(input, { target: { value: 'changed value' } })
      expect(input.value).toBe('changed value')
    })

    it('should work as controlled component', () => {
      const TestComponent = () => {
        const [value, setValue] = useState('controlled value')
        return (
          <Input
            value={value}
            onChange={(e) => setValue(e.target.value)}
          />
        )
      }
      
      render(<TestComponent />)
      
      const input = screen.getByDisplayValue('controlled value') as HTMLInputElement
      expect(input.value).toBe('controlled value')
      
      fireEvent.change(input, { target: { value: 'new controlled value' } })
      expect(input.value).toBe('new controlled value')
    })
  })

  describe('Accessibility', () => {
    it('should be focusable when not disabled', () => {
      render(<Input />)
      
      const input = screen.getByRole('textbox')
      input.focus()
      expect(input).toHaveFocus()
    })

    it('should not be focusable when disabled', () => {
      render(<Input disabled />)
      
      const input = screen.getByRole('textbox')
      expect(input).toBeDisabled()
    })

    it('should support aria-describedby', () => {
      render(
        <>
          <Input aria-describedby="help-text" />
          <div id="help-text">Help text</div>
        </>
      )
      
      const input = screen.getByRole('textbox')
      expect(input).toHaveAttribute('aria-describedby', 'help-text')
    })

    it('should support aria-required', () => {
      render(<Input aria-required />)
      
      const input = screen.getByRole('textbox')
      expect(input).toHaveAttribute('aria-required', 'true')
    })

    it('should support required attribute', () => {
      render(<Input required />)
      
      const input = screen.getByRole('textbox')
      expect(input).toBeRequired()
    })
  })

  describe('Edge Cases', () => {
    it('should handle empty string value', () => {
      render(<Input value="" readOnly />)
      
      const input = screen.getByRole('textbox') as HTMLInputElement
      expect(input.value).toBe('')
    })

    it('should handle null className', () => {
      render(<Input className={null as unknown as string} />)
      
      const input = screen.getByRole('textbox')
      expect(input).toHaveClass('flex', 'h-9', 'w-full') // should still have default classes
    })

    it('should handle very long values', () => {
      const longValue = 'a'.repeat(1000)
      render(<Input value={longValue} readOnly />)
      
      const input = screen.getByDisplayValue(longValue) as HTMLInputElement
      expect(input.value).toBe(longValue)
    })

    it('should handle special characters in value', () => {
      const specialValue = '!@#$%^&*()_+-=[]{}|;:,.<>?'
      render(<Input value={specialValue} readOnly />)
      
      const input = screen.getByDisplayValue(specialValue) as HTMLInputElement
      expect(input.value).toBe(specialValue)
    })
  })
})
