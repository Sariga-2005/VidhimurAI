import React from 'react'

interface ButtonProps {
    children: React.ReactNode
    variant?: 'primary' | 'secondary'
    size?: 'sm' | 'md' | 'lg'
    fullWidth?: boolean
    onClick?: () => void
    className?: string
}

const Button: React.FC<ButtonProps> = ({
    children,
    variant = 'primary',
    size = 'md',
    fullWidth = false,
    onClick,
    className = '',
}) => {
    const baseStyles =
        'inline-flex items-center justify-center font-semibold rounded-lg transition-all duration-300 cursor-pointer select-none focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-navy-900'

    const variants = {
        primary:
            'bg-brand hover:bg-brand-dark text-white shadow-sm hover:shadow-md active:scale-[0.99]',
        secondary:
            'border-2 border-brand text-brand hover:bg-brand-light/5 active:scale-[0.99]',
    }

    const sizes = {
        sm: 'px-4 py-2 text-sm gap-2',
        md: 'px-6 py-3 text-base gap-2',
        lg: 'px-8 py-4 text-lg gap-3',
    }

    return (
        <button
            onClick={onClick}
            className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${fullWidth ? 'w-full' : ''} ${className}`}
        >
            {children}
        </button>
    )
}

export default Button
