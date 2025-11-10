import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';
import { ProductTable } from '@/components/productos/ProductTable';
import { ProductModal } from '@/components/productos/ProductModal';

export interface Product {
  id: string;
  codigo: string;
  nombre: string;
  descripcion: string;
  categoria: string;
  unidad: string;
  stock_minimo: number;
  stock_actual: number;
}

const Productos = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | undefined>();

  useEffect(() => {
    const stored = localStorage.getItem('products');
    if (stored) {
      setProducts(JSON.parse(stored));
    } else {
      const mockData: Product[] = [
        { id: '1', codigo: 'PRD001', nombre: 'Producto A', descripcion: 'Descripción A', categoria: 'Categoría 1', unidad: 'unidades', stock_minimo: 10, stock_actual: 50 },
        { id: '2', codigo: 'PRD002', nombre: 'Producto B', descripcion: 'Descripción B', categoria: 'Categoría 2', unidad: 'cajas', stock_minimo: 5, stock_actual: 25 },
      ];
      setProducts(mockData);
      localStorage.setItem('products', JSON.stringify(mockData));
    }
  }, []);

  const handleSave = (product: Product) => {
    let updated: Product[];
    if (editingProduct) {
      updated = products.map(p => p.id === product.id ? product : p);
    } else {
      updated = [...products, { ...product, id: Date.now().toString() }];
    }
    setProducts(updated);
    localStorage.setItem('products', JSON.stringify(updated));
    setIsModalOpen(false);
    setEditingProduct(undefined);
  };

  const handleEdit = (product: Product) => {
    setEditingProduct(product);
    setIsModalOpen(true);
  };

  const handleDelete = (id: string) => {
    const updated = products.filter(p => p.id !== id);
    setProducts(updated);
    localStorage.setItem('products', JSON.stringify(updated));
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold text-foreground">Productos</h2>
        <Button onClick={() => setIsModalOpen(true)}>
          <Plus className="mr-2 h-4 w-4" /> Nuevo Producto
        </Button>
      </div>

      <ProductTable products={products} onEdit={handleEdit} onDelete={handleDelete} />
      <ProductModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setEditingProduct(undefined);
        }}
        onSave={handleSave}
        product={editingProduct}
      />
    </div>
  );
};

export default Productos;
