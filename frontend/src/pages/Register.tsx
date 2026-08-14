import React from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { z } from 'zod'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useAuth } from '../contexts/AuthContext'

const schema = z.object({
  name: z.string().min(2),
  email: z.string().email(),
  password: z.string().min(8),
})

type FormData = z.infer<typeof schema>

const Register: React.FC = () => {
  const { register: registerUser, loading } = useAuth()
  const navigate = useNavigate()
  const { register, handleSubmit, formState } = useForm<FormData>({ resolver: zodResolver(schema) })

  const onSubmit = async (data: FormData) => {
    try {
      await registerUser(data.name, data.email, data.password)
      navigate('/login')
    } catch (err: any) {
      // show safe message
      alert(err.message || 'Registration failed')
    }
  }

  return (
    <div className="container">
      <h1>Register</h1>
      <form onSubmit={handleSubmit(onSubmit)}>
        <div>
          <label>Name</label>
          <input {...register('name')} />
          {formState.errors.name && <div role="alert">{formState.errors.name.message}</div>}
        </div>
        <div>
          <label>Email</label>
          <input {...register('email')} />
          {formState.errors.email && <div role="alert">{formState.errors.email.message}</div>}
        </div>
        <div>
          <label>Password</label>
          <input type="password" {...register('password')} />
          {formState.errors.password && <div role="alert">{formState.errors.password.message}</div>}
        </div>
        <button type="submit" disabled={loading}>Register</button>
      </form>
      <p>
        Have an account? <Link to="/login">Login</Link>
      </p>
    </div>
  )
}

export default Register
