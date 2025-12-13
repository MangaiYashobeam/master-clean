String mensaje = "";
int valor[2] = {0, 100};
 
void decodificar()
{
  String Valor = mensaje;
  valor[0] = Valor.substring(0, Valor.indexOf(".")).toInt();
  valor[1] = Valor.substring(Valor.indexOf(".") + 1).toInt(); 
}
 