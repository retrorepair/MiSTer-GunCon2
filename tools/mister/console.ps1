# Minimal interactive serial console for the MiSTer UART (default COM3, 115200 8N1).
# Type into this window to talk to the MiSTer's Linux console. Quit with Ctrl+] or Ctrl+C.
# Log in yourself at the prompt; the login stays active on the MiSTer after you quit,
# so scripts that open the port afterwards land in a shell.
param([string]$Port = 'COM3', [int]$Baud = 115200)

$p = New-Object System.IO.Ports.SerialPort $Port, $Baud, 'None', 8, 'One'
$p.Open()
Write-Host "Connected to $Port @ $Baud. Press Ctrl+] to quit."
$p.Write("`r")
try {
	while ($true) {
		if ($p.BytesToRead -gt 0) { [Console]::Write($p.ReadExisting()) }
		if ([Console]::KeyAvailable) {
			$k = [Console]::ReadKey($true)
			if ($k.Key -eq 'Oem6' -and ($k.Modifiers -band [ConsoleModifiers]::Control)) { break }
			if ($k.Key -eq 'Enter') { $p.Write("`r") }
			elseif ($k.Key -eq 'Backspace') { $p.Write([string][char]127) }
			elseif ($k.KeyChar -ne [char]0) { $p.Write([string]$k.KeyChar) }
		}
		Start-Sleep -Milliseconds 10
	}
}
finally {
	if ($p.IsOpen) { $p.Close() }
	Write-Host "`nPort closed."
}
