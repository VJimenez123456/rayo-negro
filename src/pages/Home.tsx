import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Package, MapPin, ArrowDownToLine, ArrowUpFromLine } from "lucide-react";

const Home = () => {
  const stats = [
    { title: "Total Productos", value: "248", icon: Package, color: "text-primary" },
    { title: "Ubicaciones", value: "12", icon: MapPin, color: "text-accent" },
    { title: "Entradas (Mes)", value: "156", icon: ArrowDownToLine, color: "text-green-600" },
    { title: "Salidas (Mes)", value: "142", icon: ArrowUpFromLine, color: "text-red-600" },
  ];

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold text-foreground">Panel de Control</h2>
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.title}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {stat.title}
              </CardTitle>
              <stat.icon className={`h-4 w-4 ${stat.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Resumen de Inventario</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Sistema de gestión de inventario de almacén. Utiliza el menú lateral para navegar entre módulos.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default Home;
