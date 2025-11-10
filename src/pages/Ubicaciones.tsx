import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Edit, Trash2 } from 'lucide-react';

interface Location {
  id: string;
  codigo: string;
  nombre: string;
  tipo: string;
  capacidad: number;
}

const Ubicaciones = () => {
  const [locations, setLocations] = useState<Location[]>([]);

  useEffect(() => {
    const stored = localStorage.getItem('locations');
    if (stored) {
      setLocations(JSON.parse(stored));
    } else {
      const mockData: Location[] = [
        { id: '1', codigo: 'A-01', nombre: 'Pasillo A - Estante 1', tipo: 'Estantería', capacidad: 100 },
        { id: '2', codigo: 'B-02', nombre: 'Pasillo B - Estante 2', tipo: 'Estantería', capacidad: 150 },
      ];
      setLocations(mockData);
      localStorage.setItem('locations', JSON.stringify(mockData));
    }
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold text-foreground">Ubicaciones</h2>
        <Button>
          <Plus className="mr-2 h-4 w-4" /> Nueva Ubicación
        </Button>
      </div>

      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Código</TableHead>
              <TableHead>Nombre</TableHead>
              <TableHead>Tipo</TableHead>
              <TableHead className="text-right">Capacidad</TableHead>
              <TableHead className="text-right">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {locations.map((location) => (
              <TableRow key={location.id}>
                <TableCell className="font-medium">{location.codigo}</TableCell>
                <TableCell>{location.nombre}</TableCell>
                <TableCell>{location.tipo}</TableCell>
                <TableCell className="text-right">{location.capacidad}</TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-2">
                    <Button variant="ghost" size="icon">
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon">
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
};

export default Ubicaciones;
