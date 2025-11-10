import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { DashboardLayout } from "@/components/DashboardLayout";
import Login from "./pages/Login";
import Home from "./pages/Home";
import Productos from "./pages/Productos";
import Ubicaciones from "./pages/Ubicaciones";
import Inventarios from "./pages/Inventarios";
import Entradas from "./pages/Entradas";
import Salidas from "./pages/Salidas";
import Usuarios from "./pages/Usuarios";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <AuthProvider>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={
              <ProtectedRoute>
                <DashboardLayout><Home /></DashboardLayout>
              </ProtectedRoute>
            } />
            <Route path="/productos" element={
              <ProtectedRoute>
                <DashboardLayout><Productos /></DashboardLayout>
              </ProtectedRoute>
            } />
            <Route path="/ubicaciones" element={
              <ProtectedRoute>
                <DashboardLayout><Ubicaciones /></DashboardLayout>
              </ProtectedRoute>
            } />
            <Route path="/inventarios" element={
              <ProtectedRoute>
                <DashboardLayout><Inventarios /></DashboardLayout>
              </ProtectedRoute>
            } />
            <Route path="/entradas" element={
              <ProtectedRoute>
                <DashboardLayout><Entradas /></DashboardLayout>
              </ProtectedRoute>
            } />
            <Route path="/salidas" element={
              <ProtectedRoute>
                <DashboardLayout><Salidas /></DashboardLayout>
              </ProtectedRoute>
            } />
            <Route path="/usuarios" element={
              <ProtectedRoute>
                <DashboardLayout><Usuarios /></DashboardLayout>
              </ProtectedRoute>
            } />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </AuthProvider>
  </QueryClientProvider>
);

export default App;
