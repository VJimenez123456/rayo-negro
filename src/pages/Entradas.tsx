import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { format } from 'date-fns';

const Entradas = () => {
  const entradas = [
    { id: '1', producto: 'Producto A', cantidad: 50, fecha: new Date(), usuario: 'Admin' },
    { id: '2', producto: 'Producto B', cantidad: 30, fecha: new Date(), usuario: 'Admin' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold text-foreground">Entradas de Inventario</h2>
        <Button>
          <Plus className="mr-2 h-4 w-4" /> Nueva Entrada
        </Button>
      </div>

      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Producto</TableHead>
              <TableHead className="text-right">Cantidad</TableHead>
              <TableHead>Fecha</TableHead>
              <TableHead>Usuario</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {entradas.map((entrada) => (
              <TableRow key={entrada.id}>
                <TableCell className="font-medium">{entrada.producto}</TableCell>
                <TableCell className="text-right">{entrada.cantidad}</TableCell>
                <TableCell>{format(entrada.fecha, 'dd/MM/yyyy HH:mm')}</TableCell>
                <TableCell>{entrada.usuario}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
};

export default Entradas;
