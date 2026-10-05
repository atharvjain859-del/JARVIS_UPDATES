using System.IO.Ports;

namespace Jarvis.Native;

public sealed class JarvisApp
{
    public void Run()
    {
        Console.WriteLine("JARVIS Native 8.0.0");
        Console.WriteLine("Python runtime is not required.");
        Console.WriteLine("Arduino bridge: waiting for a compatible COM port.");

        foreach (var port in SerialPort.GetPortNames())
            Console.WriteLine($"Detected: {port}");

        // Deliberately does not open or modify a COM port automatically.
        // Device selection and external actions remain explicit.
    }
}
