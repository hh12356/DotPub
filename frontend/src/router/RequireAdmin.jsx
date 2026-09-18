import { Navigate } from 'react-router-dom'
import { getUserRole } from '@/utils/userRole'

const RequireAdmin = ({ children }) =>
    getUserRole() === 'admin' ? children : <Navigate to="/" replace />

export default RequireAdmin
