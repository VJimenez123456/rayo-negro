import { Card } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';

const Inventarios = () => {
  const inventarios = [
    { id: '1', producto: 'Producto A', ubicacion: 'A-01', cantidad: 50, estado: 'Normal' },
    { id: '2', producto: 'Producto B', ubicacion: 'B-02', cantidad: 8, estado: 'Bajo' },
  ];

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold text-foreground">Inventarios</h2>

      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Producto</TableHead>
              <TableHead>Ubicación</TableHead>
              <TableHead className="text-right">Cantidad</TableHead>
              <TableHead>Estado</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {inventarios.map((item) => (
              <TableRow key={item.id}>
                <TableCell className="font-medium">{item.producto}</TableCell>
                <TableCell>{item.ubicacion}</TableCell>
                <TableCell className="text-right">{item.cantidad}</TableCell>
                <TableCell>
                  <Badge variant={item.estado === 'Normal' ? 'default' : 'destructive'}>
                    {item.estado}
                  </Badge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
};

export default Inventarios;
